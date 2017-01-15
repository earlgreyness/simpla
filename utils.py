import transliterate

import parser
import simpla


def _construct_url(name):
    _name = name.strip().lower().replace(' ', '-')
    label = transliterate.translit(_name, 'ru', reversed=True)
    return ''.join(ch for ch in label if ch.isalpha() or ch.isdigit() or ch == '-')


def remove_invisible():
    simpla.db.session.query(simpla.Category).filter_by(visible=0).delete()
    simpla.db.session.commit()


def show_invisible():
    db = simpla.db
    Category = simpla.Category

    categories = (
        db.session.query(Category)
                  .filter(Category.visible == 0)
                  .order_by(Category.parent_id, Category.id)
                  .all()
    )

    for category in categories:
        print(category)


def add_categories_from_file(filename):
    Category = simpla.Category
    db = simpla.db

    data = parser.parse(filename)

    def create(name, parent_id):
        c = Category(
            name=name,
            meta_title=name,
            meta_keywords=name,
            url=_construct_url(name),
            visible=0,
            parent_id=parent_id,
        )
        db.session.add(c)
        db.session.flush()
        return c

    try:
        for group in data:
            parent = create(group['parent'], parent_id=0)
            children = [create(name, parent_id=parent.id) for name in group['children']]
            for category in ([parent] + children):
                category.position = category.id

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise


if __name__ == '__main__':
    # remove_invisible()
    # add_categories_from_file('Categories.xlsx')
    show_invisible()
