import time
import logging

class PurchaseCache:
    def __init__(self, db):
        self.db = db  # 这里传入的是LibraryDatabase实例
        self._index = []
        self._books_cache = []
        self.last_refresh = 0
        self.total = 0
        self.ids_cache = []
        self.amount = 0
        
    def _refresh(self):
        """刷新采购书籍缓存"""
        if time.time() - self.last_refresh > 3600:
            sql_purchase = """SELECT id FROM custom_columns WHERE label = 'purchase'"""
            # 修改这里 - 使用self.db而不是self.cache
            rows_purchase = self.db.backend.conn.get(sql_purchase)

            sql_readStatus = """SELECT id FROM custom_columns WHERE label = 'readStatus'"""
            rows_readStatus = self.db.backend.conn.get(sql_readStatus)

            books = []
            ids = []
            amount = 0
            if rows_purchase:
                col_id_purchase = rows_purchase[0][0]
                table_name_purchase = f"custom_column_{col_id_purchase}"

                col_id_readStatus = rows_readStatus[0][0]
                table_name_readStatus = f"custom_column_{col_id_readStatus}"

                tuple_list = []

                sql = f"""
                SELECT A.book, B.title, A.value, A.purchase_date, B.isbn, C.value AS read_status 
                FROM {table_name_purchase} as A 
                LEFT JOIN books as B ON B.id = A.book 
                LEFT JOIN {table_name_readStatus} AS C ON C.book = A.book
                WHERE CAST(A.value AS REAL) > 0 
                group by A.book
                """

                logging.debug("db操作 - PurchaseCache - sql: ")
                logging.debug(sql)
                tuple_list = self.db.backend.conn.get(sql)
                # [(50, 10.8, '书名', ''), (51, 5.0, '书名', '')]
                
                for book in tuple_list:
                    item = {
                        "id": book[0], 
                        "title": book[1], 
                        "price": book[2], 
                        "purchase_date": book[3],
                        "isbn": book[4],
                        "readStatus": book[5],
                        "rating": "",
                        "timestamp": "",
                        "pubdate": "",
                        "author": "",
                        "authors": "",
                        "author_sort": "",
                        "tag": "",
                        "tags": "",
                        "publisher": "",
                        "comments": "",
                        "series": "",
                        "language": "",
                        "img": "",
                        "thumb": "",
                        "collector": "",
                        "count_visit": "",
                        "count_download": "",
                    }
                    books.append(item)
                    ids.append(item['id'])
                    if item['price'] and float(item['price']) > 0:
                        amount += round(float(item['price']), 2)
                
                # 存储到缓存
                self._books_cache = books
                self.ids_cache = ids
                self.total = len(books)
                self.amount = round(amount, 2)
                self.last_refresh = time.time()
    
    def get_ids(self):
        """获取所有采购书籍ID"""
        self._refresh()
        return self._index

    def get_amount(self, query=None):
        """采购书籍总价"""
        self._refresh()
        return self.amount

    def clear_cache(self, query=None):
        """清空采购书籍缓存"""
        self.last_refresh = 0
        self.total = 0
        
    def search(self, query=None):
        """搜索采购书籍"""
        self._refresh()
        return self.ids_cache

    def get_books(self, *args, **kwargs):
        """获取缓存的采购书籍数据"""
        self._refresh()
        if 'ids' in kwargs and kwargs['ids']:
            # 只返回kwargs中指定ID的书籍
            return [book for book in self._books_cache if book['id'] in kwargs['ids']]
        else:
            # 返回所有缓存的书籍
            return self._books_cache

class WishCache:
    def __init__(self, db):
        self.db = db  # 这里传入的是LibraryDatabase实例
        self._index = []
        self._books_cache = []
        self.last_refresh = 0
        self.total = 0
        self.ids_cache = []
        
    def _refresh(self):
        """刷新心愿书籍缓存"""
        if time.time() - self.last_refresh > 3600:
            sql_wish = """SELECT id FROM custom_columns WHERE label = 'wish'"""
            # 修改这里 - 使用self.db而不是self.cache
            rows_wish = self.db.backend.conn.get(sql_wish)

            logging.debug("db操作 - WishCache - sql_wish:: ")

            sql_readStatus = """SELECT id FROM custom_columns WHERE label = 'readStatus'"""
            rows_readStatus = self.db.backend.conn.get(sql_readStatus)

            books = []
            ids = []
            if rows_wish:
                col_id_wish = rows_wish[0][0]
                table_name_wish = f"custom_column_{col_id_wish}"

                col_id_readStatus = rows_readStatus[0][0]
                table_name_readStatus = f"custom_column_{col_id_readStatus}"

                tuple_list = []

                sql = f"""
                SELECT A.book, B.title, A.value, B.isbn, C.value AS read_status 
                FROM {table_name_wish} as A 
                LEFT JOIN books as B ON B.id = A.book 
                LEFT JOIN {table_name_readStatus} AS C ON C.book = A.book
                WHERE CAST(A.value AS REAL) > 0 
                group by A.book
                """

                logging.debug("db操作 - get_wish_list() - sql: ")
                logging.debug(sql)
                tuple_list = self.db.backend.conn.get(sql)
                # [(50, 10.8, '书名', ''), (51, 5.0, '书名', '')]
                
                for book in tuple_list:
                    item = {
                        "id": book[0], 
                        "title": book[1],
                        "wish": "",
                        "isbn": book[3],
                        "readStatus": book[4],
                        "rating": "",
                        "timestamp": "",
                        "pubdate": "",
                        "author": "",
                        "authors": "",
                        "author_sort": "",
                        "tag": "",
                        "tags": "",
                        "publisher": "",
                        "comments": "",
                        "series": "",
                        "language": "",
                        "img": "",
                        "thumb": "",
                        "collector": "",
                        "count_visit": "",
                        "count_download": "",
                    }
                    if book[2] == 1:
                        item["wish"] = "是"
                    else:
                        item["wish"] = "否"
                    books.append(item)
                    ids.append(item['id'])
                
                # 存储到缓存
                self._books_cache = books
                self.ids_cache = ids
                self.total = len(books)
                self.last_refresh = time.time()
    
    def get_ids(self):
        """获取所有心愿书籍ID"""
        self._refresh()
        return self._index
        
    def search(self, query=None):
        """搜索心愿书籍"""
        self._refresh()
        return self.ids_cache

    def clear_cache(self, query=None):
        """清空心愿书籍缓存"""
        self.last_refresh = 0
        self.total = 0

    def get_books(self, *args, **kwargs):
        """获取缓存的心愿书籍数据"""
        self._refresh()
        if 'ids' in kwargs and kwargs['ids']:
            # 只返回kwargs中指定ID的书籍
            return [book for book in self._books_cache if book['id'] in kwargs['ids']]
        else:
            # 返回所有缓存的书籍
            return self._books_cache