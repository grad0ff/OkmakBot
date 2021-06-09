class ShoppingList:
    COUNT = 0
    __PRODUCTS = set()

    def __init__(self):
        self.shoplist = set()
        self.not_added_list = ShoppingList.__PRODUCTS
        ShoppingList.COUNT += 1

    def update_data(self):
        self.not_added_list = ShoppingList.__PRODUCTS.difference(self.shoplist)

    def add_to_shoplist(self, item):
        self.shoplist.add(item)
        self.update_data()
        print('В списке: ', self.shoplist)
        print('Не в списке: ', self.not_added_list)

    def del_from_shoplist(self, item):
        self.shoplist.remove(item)
        self.update_data()
        print('Удалено из списка: ', item)

    def add_new_item(self, new_item):
        ShoppingList.__PRODUCTS.add(new_item)
        self.add_to_shoplist(new_item)
        self.update_data()

    def delete_item(self, item):
        ShoppingList.__PRODUCTS.remove(item)
        if item in self.shoplist:
            self.shoplist.remove(item)
        self.update_data()

    def get_all_items(self):
        return ShoppingList.__PRODUCTS
