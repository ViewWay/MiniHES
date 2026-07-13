"""PDF 导出服务。

使用 reportlab 生成 PDF 格式的分析报告和测试报告。
"""

import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_daily_analysis_pdf(data: dict) -> bytes:
    """生成日线分析 PDF 报告。

    参数:
        data: 分析数据字典（包含 meter_name, date, energy, daily_billing 等）

    返回:
        PDF 文件二进制内容
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements: list = []

    # ─── 标题 ───
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=10,
    )
    elements.append(Paragraph("电表日线分析报告", title_style))
    elements.append(Spacer(1, 10))

    # ─── 基本信息 ───
    info_data = [
        ["电表名称", str(data.get("meter_name", "—"))],
        ["电表 ID", str(data.get("meter_id", "—"))],
        ["分析日期", str(data.get("date", datetime.now().strftime("%Y-%m-%d")))],
        ["总用电量", str(data.get("total_energy", "—"))],
        ["功率因数", str(data.get("power_factor", "—"))],
    ]
    info_table = Table(info_data, colWidths=[40 * mm, 100 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # ─── 24 小时用电曲线 ───
    elements.append(Paragraph("24 小时用电量", styles["Heading2"]))
    energy_data = data.get("energy", [])
    hours = data.get("hours", [f"{h:02d}:00" for h in range(24)])

    if energy_data:
        table_data = [["时间", "用电量"]]
        for i, val in enumerate(energy_data[:24]):
            table_data.append([hours[i] if i < len(hours) else f"{i}:00", str(val)])

        energy_table = Table(table_data, colWidths=[40 * mm, 60 * mm])
        energy_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ]
            )
        )
        elements.append(energy_table)
    else:
        elements.append(Paragraph("（无用电数据）", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # ─── 瞬时量 ───
    instantaneous = data.get("instantaneous", {})
    if instantaneous:
        elements.append(Paragraph("瞬时量数据", styles["Heading2"]))
        inst_data = [["参数", "值"]]
        for key, val in list(instantaneous.items())[:20]:
            inst_data.append([key, str(val)])

        inst_table = Table(inst_data, colWidths=[80 * mm, 60 * mm])
        inst_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2196F3")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ]
            )
        )
        elements.append(inst_table)

    # ─── 页脚 ───
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | MiniHES", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_test_report_pdf(data: dict) -> bytes:
    """生成测试报告 PDF。

    参数:
        data: 测试报告字典（包含 test_name, test_type, conclusion, notes 等）

    返回:
        PDF 文件二进制内容
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements: list = []

    # 标题
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=18, spaceAfter=10)
    elements.append(Paragraph(str(data.get("title", "测试报告")), title_style))
    elements.append(Spacer(1, 10))

    # 基本信息
    conclusion = data.get("conclusion", "")
    conclusion_label = "通过" if conclusion == "pass" else "不通过" if conclusion == "fail" else "—"

    info_data = [
        ["报告编号", str(data.get("report_number", "—"))],
        ["测试类型", str(data.get("test_type", "—"))],
        ["测试环境", str(data.get("test_environment", "—"))],
        ["固件版本", str(data.get("firmware_version", "—"))],
        ["硬件版本", str(data.get("hardware_version", "—"))],
        ["测试结论", conclusion_label],
    ]
    info_table = Table(info_data, colWidths=[40 * mm, 120 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # 备注
    notes = data.get("notes", "")
    if notes:
        elements.append(Paragraph("备注", styles["Heading2"]))
        elements.append(Paragraph(notes, styles["Normal"]))

    # 页脚
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | MiniHES", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
