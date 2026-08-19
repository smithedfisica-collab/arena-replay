from flask import Blueprint, render_template, request, redirect
from routes.auth import login_required
from database.database import get_connection

import secrets


print("ARQUIVO rentals.py CARREGADO")


# ======================================================
# BLUEPRINT
# ======================================================

rentals_bp = Blueprint(
    "rentals",
    __name__
)


# ======================================================
# LISTAR ALUGUÉIS
# ======================================================

@rentals_bp.route("/rentals")
@login_required
def rentals():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """

        SELECT *

        FROM rentals

        ORDER BY

            CASE

                WHEN UPPER(TRIM(status)) = 'EM ANDAMENTO'
                THEN 1

                WHEN UPPER(TRIM(status)) = 'AGENDADO'
                THEN 2

                WHEN UPPER(TRIM(status)) = 'FINALIZADO'
                THEN 4

                WHEN UPPER(TRIM(status)) = 'CANCELADO'
                THEN 5

                ELSE 3

            END ASC,

            CASE

                WHEN UPPER(TRIM(status)) IN (
                    'FINALIZADO',
                    'CANCELADO'
                )
                THEN 1

                ELSE 0

            END ASC,

            scheduled_date ASC,

            scheduled_time ASC

        """
    )

    rentals = cursor.fetchall()

    conn.close()

    return render_template(
        "rentals.html",
        rentals=rentals
    )


# ======================================================
# CRIAR / EDITAR ALUGUEL
# ======================================================

@rentals_bp.route(
    "/rentals/create",
    methods=["POST"]
)
@login_required
def create_rental():

    rental_id = request.form.get(
        "rental_id"
    )

    customer = request.form.get(
        "customer_name"
    )

    phone = request.form.get(
        "phone"
    )

    court = request.form.get(
        "court"
    )

    date = request.form.get(
        "scheduled_date"
    )

    time = request.form.get(
        "scheduled_time"
    )

    duration = request.form.get(
        "duration"
    )

    conn = get_connection()
    cursor = conn.cursor()


    # ==================================================
    # EDITAR
    # ==================================================

    if rental_id:

        cursor.execute(
            """

            UPDATE rentals

            SET

                customer_name = ?,

                phone = ?,

                court = ?,

                scheduled_date = ?,

                scheduled_time = ?,

                duration = ?

            WHERE id = ?

            """,
            (

                customer,

                phone,

                court,

                date,

                time,

                duration,

                rental_id

            )
        )

        print(
            f"ALUGUEL {rental_id} ATUALIZADO!"
        )


    # ==================================================
    # NOVO ALUGUEL
    # ==================================================

    else:

        public_token = secrets.token_hex(
            8
        )

        cursor.execute(
            """

            INSERT INTO rentals

            (

                customer_name,

                phone,

                court,

                scheduled_date,

                scheduled_time,

                duration,

                status,

                public_token

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            """,
            (

                customer,

                phone,

                court,

                date,

                time,

                duration,

                "AGENDADO",

                public_token

            )
        )

        print("=" * 60)
        print("NOVO ALUGUEL CRIADO!")
        print("CLIENTE:", customer)
        print("TOKEN:", public_token)
        print("=" * 60)


    conn.commit()
    conn.close()

    return redirect(
        "/rentals"
    )


# ======================================================
# INICIAR ALUGUEL
# ======================================================

@rentals_bp.route(
    "/rentals/start/<int:rental_id>",
    methods=["POST"]
)
@login_required
def start_rental(rental_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """

        UPDATE rentals

        SET

            status = ?,

            actual_start = CURRENT_TIMESTAMP

        WHERE id = ?

        """,
        (

            "EM ANDAMENTO",

            rental_id

        )
    )

    conn.commit()
    conn.close()

    print(
        f"ALUGUEL {rental_id} INICIADO!"
    )

    return redirect(
        "/rentals"
    )


# ======================================================
# FINALIZAR ALUGUEL
# ======================================================

@rentals_bp.route(
    "/rentals/finish/<int:rental_id>",
    methods=["POST"]
)
@login_required
def finish_rental(rental_id):

    print("=" * 60)
    print("FINALIZANDO ALUGUEL")
    print("RENTAL ID:", rental_id)
    print("=" * 60)


    # ==================================================
    # FINALIZAR O ALUGUEL NO BANCO
    # ==================================================

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """

        UPDATE rentals

        SET

            status = ?,

            actual_end = CURRENT_TIMESTAMP

        WHERE id = ?

        """,
        (

            "FINALIZADO",

            rental_id

        )
    )

    conn.commit()
    conn.close()

    print(
        f"ALUGUEL {rental_id} FINALIZADO!"
    )


    # ==================================================
    # GERAR E SALVAR REPLAY AUTOMATICAMENTE
    # ==================================================

    try:

        print("=" * 60)
        print("INICIANDO SALVAMENTO AUTOMÁTICO DO REPLAY")
        print("RENTAL ID:", rental_id)
        print("=" * 60)

        from routes.api import save_replay_for_rental

        print(
            "FUNÇÃO save_replay_for_rental ENCONTRADA"
        )

        replay_result = save_replay_for_rental(
            rental_id
        )

        print("=" * 60)
        print("RESULTADO DO SALVAMENTO DO REPLAY:")
        print(replay_result)
        print("=" * 60)


    except Exception as e:

        import traceback

        print("=" * 60)
        print("ERRO AO GERAR REPLAY AUTOMÁTICO")
        print("TIPO DO ERRO:", type(e).__name__)
        print("MENSAGEM:", str(e))
        print("=" * 60)

        traceback.print_exc()

        print("=" * 60)


    return redirect(
        "/rentals"
    )


# ======================================================
# ADICIONAR TEMPO
# ======================================================

@rentals_bp.route(
    "/rentals/add-time",
    methods=["POST"]
)
@login_required
def add_time():

    rental_id = request.form.get(
        "rental_id"
    )

    extra_duration = int(
        request.form.get(
            "extra_duration"
        )
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """

        UPDATE rentals

        SET

            extra_duration =
                COALESCE(extra_duration, 0)
                +
                ?

        WHERE id = ?

        """,
        (

            extra_duration,

            rental_id

        )
    )

    conn.commit()
    conn.close()

    print(
        f"FORAM ADICIONADOS {extra_duration} MINUTOS "
        f"AO ALUGUEL {rental_id}"
    )

    return redirect(
        "/rentals"
    )


# ======================================================
# CANCELAR ALUGUEL
# ======================================================

@rentals_bp.route(
    "/rentals/cancel/<int:rental_id>",
    methods=["POST"]
)
@login_required
def cancel_rental(rental_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """

        UPDATE rentals

        SET

            status = ?

        WHERE id = ?

        """,
        (

            "CANCELADO",

            rental_id

        )
    )

    conn.commit()
    conn.close()

    print(
        f"ALUGUEL {rental_id} CANCELADO!"
    )

    return redirect(
        "/rentals"
    )


# ======================================================
# REMOVER ALUGUEL
# ======================================================

@rentals_bp.route(
    "/rentals/delete/<int:rental_id>",
    methods=["POST"]
)
@login_required
def delete_rental(rental_id):

    conn = get_connection()
    cursor = conn.cursor()


    # ==================================================
    # REMOVE PRIMEIRO OS REPLAYS RELACIONADOS
    # ==================================================

    cursor.execute(
        """

        DELETE FROM replays

        WHERE rental_id = ?

        """,
        (

            rental_id,

        )
    )


    # ==================================================
    # REMOVE O ALUGUEL
    # ==================================================

    cursor.execute(
        """

        DELETE FROM rentals

        WHERE id = ?

        """,
        (

            rental_id,

        )
    )

    conn.commit()
    conn.close()

    print(
        f"ALUGUEL {rental_id} REMOVIDO!"
    )

    return redirect(
        "/rentals"
    )


# ======================================================
# PÁGINA PÚBLICA DO REPLAY
# ======================================================

@rentals_bp.route(
    "/r/<public_token>"
)
def public_replay(public_token):

    conn = get_connection()
    cursor = conn.cursor()


    # ==================================================
    # BUSCAR RESERVA
    # ==================================================

    cursor.execute(
        """

        SELECT

            id,

            customer_name,

            phone,

            court,

            scheduled_date,

            scheduled_time,

            duration,

            status,

            public_token

        FROM rentals

        WHERE public_token = ?

        """,
        (

            public_token,

        )
    )

    rental = cursor.fetchone()

    conn.close()


    # ==================================================
    # RESERVA NÃO ENCONTRADA
    # ==================================================

    if rental is None:

        return (
            "Reserva não encontrada.",
            404
        )


    # ==================================================
    # ABRIR PÁGINA
    # ==================================================

    return render_template(
        "replay.html",
        rental=rental,
        public_token=public_token
    )