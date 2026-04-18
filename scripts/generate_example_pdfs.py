from __future__ import annotations

from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "documents" / "example_pack"


def create_pdf(filename: str, title: str, lines: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    title_rect = fitz.Rect(50, 40, 545, 100)
    body_rect = fitz.Rect(50, 110, 545, 792)

    page.insert_textbox(title_rect, title, fontsize=16, fontname="helv", align=0)
    page.insert_textbox(body_rect, "\n".join(lines), fontsize=11, fontname="helv", align=0)

    target = OUTPUT_DIR / filename
    doc.save(target)
    doc.close()


def main() -> None:
    create_pdf(
        filename="anexo_mantenimiento_epsilon.pdf",
        title="ANEXO DE MANTENIMIENTO - EPSILON CLOUD",
        lines=[
            "1. Cobertura del servicio",
            "El proveedor cubrira mantenimiento preventivo y correctivo de infraestructura cloud.",
            "",
            "2. Ventanas de mantenimiento",
            "Las ventanas programadas seran los domingos entre 02:00 y 05:00 UTC.",
            "",
            "3. SLA y penalizaciones",
            "Disponibilidad mensual comprometida: 99.9%.",
            "Si la disponibilidad baja de 99.5%, se aplica credito del 10% de la factura mensual.",
            "",
            "4. Notificacion",
            "El proveedor notificara mantenimientos programados con al menos 72 horas de antelacion.",
        ],
    )

    create_pdf(
        filename="contrato_licencia_zeta.pdf",
        title="CONTRATO DE LICENCIA DE SOFTWARE - ZETA APPS",
        lines=[
            "1. Alcance de la licencia",
            "Licencia anual no exclusiva para 120 usuarios nombrados.",
            "",
            "2. Renovacion",
            "La renovacion sera automatica salvo aviso por escrito con 60 dias de antelacion al vencimiento.",
            "",
            "3. Soporte",
            "Soporte en horario laboral con tiempo de primera respuesta maximo de 8 horas habiles.",
            "",
            "4. Incumplimiento de pago",
            "Si existe retraso superior a 30 dias, el licenciante podra suspender acceso previo aviso de 7 dias.",
        ],
    )


if __name__ == "__main__":
    main()
