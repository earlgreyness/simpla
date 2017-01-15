import openpyxl


def _retrieve_data(sheet):
    for column in sheet.columns:
        rows = iter(column)
        parent = next(rows).value
        if not parent:
            continue
        yield dict(
            parent=parent,
            children=[item.value.strip() for item in rows if item.value],
        )


def parse(filename):
    wb = openpyxl.load_workbook(filename=filename)
    ws = wb.active
    return list(_retrieve_data(ws))
