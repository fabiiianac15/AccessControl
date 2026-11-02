"""Comandos de operación: `portero serve`, `portero admin`, `portero audit`..."""

from __future__ import annotations

import argparse
import getpass
import random
import sys
from datetime import timedelta

from . import __version__, crypto, ledger
from .biometrics.engine import ensure_models
from .config import Settings
from .db import connect, migrate, tx


def _conn(settings: Settings):
    conn = connect(settings.db_path)
    migrate(conn)
    return conn


def cmd_serve(args: argparse.Namespace, settings: Settings) -> int:
    import uvicorn

    from .web.app import create_app

    app = create_app(settings)
    # Un solo proceso: las sesiones de kiosco y la galería viven en memoria.
    uvicorn.run(
        app,
        host=args.host or settings.host,
        port=args.port or settings.port,
        proxy_headers=True,
        server_header=False,
    )
    return 0


def cmd_models(_: argparse.Namespace, settings: Settings) -> int:
    ensure_models(settings.models_dir)
    print(f"Modelos listos en {settings.models_dir}")
    return 0


def cmd_admin(args: argparse.Namespace, settings: Settings) -> int:
    password = args.password or getpass.getpass("Contraseña (mínimo 12 caracteres): ")
    if len(password) < 12:
        print("La contraseña debe tener al menos 12 caracteres.", file=sys.stderr)
        return 1
    keys = crypto.load_keyring(settings.master_key, settings.data_dir)
    conn = _conn(settings)
    exists = conn.execute("SELECT id FROM admins WHERE username = ?", (args.username,)).fetchone()
    if exists:
        conn.execute(
            """UPDATE admins SET password_hash = ?, role = ?, failed_logins = 0, locked_until = NULL
               WHERE id = ?""",
            (crypto.hash_password(password), args.role, exists["id"]),
        )
        conn.execute("DELETE FROM sessions WHERE admin_id = ?", (exists["id"],))
        action = "admin.reset"
    else:
        conn.execute(
            "INSERT INTO admins (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (args.username, crypto.hash_password(password), args.role, ledger.iso(ledger.utcnow())),
        )
        action = "admin.create"
    ledger.record_audit(conn, keys.chain_key, "cli", action, args.username, args.role)
    print(f"Cuenta {args.username} lista con rol {args.role}.")
    return 0


def cmd_audit(_: argparse.Namespace, settings: Settings) -> int:
    keys = crypto.load_keyring(settings.master_key, settings.data_dir)
    conn = _conn(settings)
    failed = False
    for report in (
        ledger.verify_events(conn, keys.chain_key),
        ledger.verify_audit(conn, keys.chain_key),
    ):
        if report.ok:
            print(f"{report.table}: íntegra ({report.rows} filas)")
        else:
            failed = True
            print(f"{report.table}: ROTA en la fila {report.broken_id}. {report.detail}")
    return 1 if failed else 0


def cmd_purge(_: argparse.Namespace, settings: Settings) -> int:
    from .people import purge_expired

    keys = crypto.load_keyring(settings.master_key, settings.data_dir)
    result = purge_expired(_conn(settings), settings, keys.chain_key, ledger.utcnow())
    print(f"Eventos borrados: {result['events']}. Fotos borradas: {result['photos']}.")
    return 0


_DEMO_PEOPLE = [
    ("Camilo Quintero", "Laboratorio de Redes"),
    ("Laura Sanjuán", "Laboratorio de Redes"),
    ("Diego Pacheco", "Docentes"),
    ("Yeimy Carrascal", "Docentes"),
    ("Andrés Ropero", "Monitores"),
    ("Natalia Ascanio", "Monitores"),
    ("Sergio Lobo", "Laboratorio de Redes"),
    ("Karen Bayona", "Administrativos"),
    ("Julián Sepúlveda", "Laboratorio de Redes"),
    ("Paola Navarro", "Administrativos"),
    ("Óscar Claro", "Docentes"),
    ("Mónica Rincón", "Monitores"),
]


def cmd_demo(_: argparse.Namespace, settings: Settings) -> int:
    """Llena una instalación vacía con datos inventados, sin biometría, para explorar el panel."""
    keys = crypto.load_keyring(settings.master_key, settings.data_dir)
    conn = _conn(settings)
    if conn.execute("SELECT 1 FROM people LIMIT 1").fetchone():
        print(
            "La base ya tiene personas: la demostración solo corre sobre una instalación vacía.",
            file=sys.stderr,
        )
        return 1

    rng = random.Random(1581)  # noqa: S311 - datos de ejemplo reproducibles
    now = ledger.utcnow()
    tz = settings.tz
    with tx(conn):
        zones = [
            conn.execute("INSERT INTO zones (name, description) VALUES (?, ?)", row).lastrowid
            for row in (
                ("Laboratorio de Redes", "Bloque de ingenierías, piso 2"),
                ("Sala de Servidores", "Solo personal autorizado"),
            )
        ]
        kiosks = [
            conn.execute(
                """INSERT INTO kiosks (name, zone_id, token_hash, last_seen_at)
                   VALUES (?, ?, ?, ?)""",
                (name, zone, crypto.token_hash(crypto.new_token()), ledger.iso(now)),
            ).lastrowid
            for name, zone in (("Entrada laboratorio", zones[0]), ("Puerta servidores", zones[1]))
        ]
        people = []
        for name, group in _DEMO_PEOPLE:
            person = conn.execute(
                """INSERT INTO people (full_name, group_name, pin_lookup, created_at)
                   VALUES (?, ?, ?, ?)""",
                # El PIN de cada persona es aleatorio y no se muestra: nadie entra con la demo.
                (
                    name,
                    group,
                    keys.pin_lookup(crypto.new_token()),
                    ledger.iso(now - timedelta(days=45)),
                ),
            ).lastrowid
            people.append(person)
            conn.execute(
                """INSERT INTO grants (person_id, zone_id, weekdays, start_minute, end_minute)
                   VALUES (?, ?, 31, 360, 1200)""",
                (person, zones[0]),
            )

        local_today = now.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        moments = []
        for days_ago in range(30, -1, -1):
            day = local_today - timedelta(days=days_ago)
            if day.weekday() >= 5 and days_ago > 0:  # hoy siempre tiene movimiento, para el tablero
                continue
            for person in people:
                if rng.random() > 0.8:
                    continue
                arrival = day + timedelta(minutes=rng.gauss(7.5 * 60, 40))
                moments.append((arrival, person, "granted", "ok"))
                moments.append(
                    (arrival + timedelta(hours=rng.uniform(3, 9)), person, "granted", "ok")
                )
                if rng.random() < 0.08:
                    moments.append(
                        (
                            arrival + timedelta(minutes=rng.uniform(5, 300)),
                            person,
                            "denied",
                            rng.choice(["outside_schedule", "no_grant"]),
                        )
                    )
            for _attempt in range(rng.randint(0, 3)):
                stamp = day + timedelta(minutes=rng.uniform(6 * 60, 20 * 60))
                moments.append(
                    (
                        stamp,
                        None,
                        "denied",
                        rng.choice(["unknown_face", "unknown_face", "liveness_failed"]),
                    )
                )
        for moment, person, outcome, reason in sorted(moments, key=lambda item: item[0]):
            if moment >= now:
                continue
            index = 1 if reason == "no_grant" else 0
            method = "pin" if person and rng.random() < 0.12 else "face"
            ledger.record_event(
                conn,
                keys.chain_key,
                kiosk_id=kiosks[index],
                zone_id=zones[index],
                person_id=person,
                method=method,
                outcome=outcome,
                reason="ok_pin" if method == "pin" and reason == "ok" else reason,
                score=round(rng.uniform(0.55, 0.85), 3) if person else None,
                when=moment,
            )
    print(f"Demostración cargada: {len(people)} personas y {len(moments)} eventos de 30 días.")
    print("Todas las personas son inventadas y ninguna tiene datos biométricos.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="portero", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Inicia el servidor")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.set_defaults(func=cmd_serve)

    commands.add_parser("models", help="Descarga y verifica los modelos").set_defaults(
        func=cmd_models
    )

    admin = commands.add_parser("admin", help="Crea una cuenta o restablece su contraseña")
    admin.add_argument("username")
    admin.add_argument("--role", choices=["admin", "viewer"], default="admin")
    admin.add_argument("--password", help="Para automatizar; si falta, se pide por terminal")
    admin.set_defaults(func=cmd_admin)

    commands.add_parser("audit", help="Verifica las cadenas de registros").set_defaults(
        func=cmd_audit
    )
    commands.add_parser("purge", help="Aplica la retención de datos").set_defaults(func=cmd_purge)
    commands.add_parser("demo", help="Carga datos inventados en una base vacía").set_defaults(
        func=cmd_demo
    )

    args = parser.parse_args(argv)
    return args.func(args, Settings())


if __name__ == "__main__":
    raise SystemExit(main())
