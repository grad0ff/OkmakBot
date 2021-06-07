class ShoppingList:
    COUNT = 0
    __PRODUCTS = {'A', 'B', 'C', 'D', 'E', 'F'}

    def __init__(self):
        self.shoplist = set()
        self.not_added_list = ShoppingList.__PRODUCTS
        ShoppingList.COUNT += 1

    def add_to_shoplist(self, item):
        self.shoplist.add(item)
        self.not_added_list = ShoppingList.__PRODUCTS.difference(self.shoplist)
        print('В списке: ', self.shoplist)
        print('Не в списке: ', self.not_added_list)

    def del_from_shoplist(self, item):
        self.shoplist.remove(item)
        self.not_added_list = ShoppingList.__PRODUCTS.difference(self.shoplist)
        print('Удалено: ', item)

    def add_new_item(self, new_item):
        ShoppingList.__PRODUCTS.add(new_item)

    def delete_item(self, item):
        ShoppingList.__PRODUCTS.remove(item)

    def get_all_items(self):
        return ShoppingList.__PRODUCTS