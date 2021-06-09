

class ShoppingList:
    COUNT = 0

    def __init__(self):
        self.products = set()
        self.shoplist = set()
        self.not_added_list = set()
        ShoppingList.COUNT += 1

    def update_data(self):
        self.not_added_list = self.products.difference(self.shoplist)

    def add_to_shoplist(self, item):
        self.shoplist.add(item)
        print('Добавлено в список: ', item)
        self.update_data()

    def del_from_shoplist(self, item):
        self.shoplist.remove(item)
        self.update_data()
        print('Удалено из списка: ', item)

    def add_new_item(self, new_item):
        self.products.add(new_item)
        self.add_to_shoplist(new_item)
        self.update_data()
        print('Добавлено в список и записи: ', new_item)

    def delete_item(self, item):
        self.products.remove(item)
        if item in self.shoplist:
            self.shoplist.remove(item)
            print('Удалено из записей: ', item)
        self.update_data()

    def get_all_items(self):
        return self.products
