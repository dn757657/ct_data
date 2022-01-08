import sqlite3
import pathlib
import pandas as pd
import copy
import os

fipy_fp = pathlib.Path(__file__).absolute().parent
os.makedirs(fipy_fp.joinpath('db'), exist_ok=True)


class FinanceDB:
    """    Object for interacting with the finance database object

    Attributes:
    filename:   name of the database file including filepath - hardcoded
    filepath:   file location of the db file, based on parent file of src
    conn:       database connection object
    cursor:     database cursor object
    schema:     dictionary of lists, keys are tables, values are columns

    """

    def __init__(self):
        """ create database object and populate schema data"""
        # connect to db when initialized and establish cursor for later use
        self.filename = "CTFinance.db"
        self.filepath = fipy_fp.joinpath("db")

        # must enforce foreign keys when connection is formed
        self.conn = sqlite3.connect(self.filepath.joinpath(self.filename))
        self.conn.cursor().execute('PRAGMA foreign_keys = 1')

        # access and store schema
        self.schema = dict()
        self.schema = self._get_accounts()

    def refresh_conn(self):
        self.conn.close()
        self.conn = sqlite3.connect(self.filepath.joinpath(self.filename))
        self.conn.cursor().execute('PRAGMA foreign_keys = 1')

    def _get_accounts(self):
        tables = self.conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        self.conn.cursor().close()
        schema = dict()
        # remove sqlite sequence table
        for tup in tables:
            if "sqlite_sequence" in tup:
                tables.remove(tup)
        # access and populate columns for each table name from db
        for table in tables:
            columns = list(map(lambda x: x[0], self.conn.cursor().execute("SELECT * FROM " + table[0]).description))
            schema[table[0]] = columns

        self.conn.cursor().close()
        return schema

    def _queryize_columns(self, columns_list):
        """create string compatible with injection in sql query from list of strings"""
        col_str = ""
        if columns_list:
            if len(columns_list) != 0:
                for column in columns_list:
                    if col_str == "":
                        col_str = col_str + column
                    else:
                        col_str = col_str + "," + column
        else:
            col_str = "*"

        return col_str

    def drop_duplicates(self, table, method, condition=None, new_data=None, id_col=None, filter_columns=None):
        """ Drop sql table entries based on first or last duplicate entered

        Args:
            <table>             string table name to delete duplicates
            <condition>         MIN or MAX, decides if maximum or minimum id in selected entries is not deleted
            <id_col>            which columns to use as unique id, default to first column in table schema
                                to this columns
            <filter_columns>    columns to determine if entry is unique or duplicate, if None all columns but first are
                                used as first is typically id column
        """
        if method in ['inside', 'outside']:
            # if no id_col passed, default is first column in table schema
            if not id_col:
                id_col = self.schema[table][0]

            # if not filter columns are passed than all are used except for the first [0] which is id, as all id are
            # unique and would delete nothing
            # copy.deepcopy(db.schema[query.table])
            if not filter_columns:
                columns_str = self._queryize_columns(copy.deepcopy(self.schema[table]).pop(0))
                filter_columns = copy.deepcopy(self.schema[table]).pop(0)
            else:
                columns_str = self._queryize_columns(filter_columns)

            if method == 'inside':
                if condition:
                    query = "DELETE FROM " + table + " WHERE " + id_col + " NOT IN (SELECT " + condition + \
                            "(" + id_col + ") FROM " + table + " GROUP BY " + columns_str + ")"
                    print(query)
                    self.conn.execute(query)
                    self.conn.commit()
                else:
                    print('Must provide condition when using inside method')

            elif method == 'outside':
                if not new_data.empty:
                    # select all existing table data using passed columns or default all
                    query = pd.read_sql_query("SELECT " + columns_str + " FROM " + table, self.conn)
                    existing_data = pd.DataFrame(query, columns=filter_columns)

                    # transactions table must be formatted as date to compare to new transactions data
                    if 'date' in existing_data.columns.tolist():
                        # convert to datetime
                        existing_data['date'] = pd.to_datetime(existing_data['date'])
                    if 'date' in new_data.columns.tolist():
                        new_data['date'] = pd.to_datetime(new_data['date'])

                    # merge data into single df
                    new_data = new_data.merge(existing_data, indicator=True, how='outer')
                    # merged dataframes will have _merge column indicating with dataframe contains each row
                    # drop rows where _merge column is 'both' eliminating overlap in files
                    new_data.drop(index=new_data[new_data['_merge'] == 'both'].index, inplace=True)
                    new_data.drop(index=new_data[new_data['_merge'] == 'right_only'].index, inplace=True)
                    # _merge column no longer needed
                    new_data.drop(columns=['_merge'], inplace=True)

                    # dump cleaned transactions to sql
                    new_data.to_sql(name=table, index=False, con=self.conn, if_exists='append')
                else:
                    print('Must provide new data to compare')

        else:
            print("Method must be either 'inside' or 'outside")

    def create_transactions(self,):

        # transactions has foreign keys linking to categories and accounts
        self.create_categories()
        self.create_accounts()

        transactions = """ CREATE TABLE IF NOT EXISTS transactions (
                            trans_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            desc TEXT NOT NULL,
                            amount REAL NOT NULL,
                            total_id REAL NOT NULL,
                            
                            processed INTEGER CHECK(processed IN (0,1)) DEFAULT(0),
                            
                            cat_id INTEGER DEFAULT NULL,
                            acc_id INTEGER,
                            FOREIGN KEY (cat_id) REFERENCES categories (cat_id) ON DELETE SET NULL ON UPDATE CASCADE,
                            FOREIGN KEY (acc_id) REFERENCES accounts (acc_id) ON DELETE CASCADE ON UPDATE CASCADE
                            
                        ); """

        # create slits to store originals of split transactions so they arent replicated in updates
        splits = """ CREATE TABLE IF NOT EXISTS splits (
                            trans_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            desc TEXT NOT NULL,
                            amount REAL NOT NULL,
                            total_id REAL NOT NULL
                            
                        ); """

        if 'transactions' not in self.schema.keys():
            self.conn.cursor().execute(transactions)
            print("Created transactions table")

        if 'splits' not in self.schema.keys():
            self.conn.cursor().execute(splits)
            print("Created splits table")

        # update schema!
        self.schema = self._get_accounts()

        return

    def create_categories(self,):
        categories = """ CREATE TABLE IF NOT EXISTS categories (
                            cat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cat_desc TEXT NOT NULL
    
                        ); """

        if 'categories' not in self.schema.keys():
            self.conn.cursor().execute(categories)
            print("Created categories table")

        # update schema!
        self.schema = self._get_accounts()

        return

    def create_displays(self,):
        displays = """ CREATE TABLE IF NOT EXISTS displays (
                        di_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        di_target REAL NOT NULL,
                        disp_start TEXT,
                        disp_resolution REAL TEXT CHECK(disp_resolution IN ('year', 'month', 'week', 'day')),
                        disp_end TEXT,
                        disp_window_size INTEGER,
                        disp_window_unit TEXT CHECK(disp_window_unit IN ('year', 'month', 'week', 'day')),
                        disp_type TEXT NOT NULL,
                        graph_type TEXT NOT NULL,
                        proj_type TEXT,
                        di_cat INTEGER NOT NULL,
                        FOREIGN KEY (di_cat) REFERENCES categories (cat_id) ON DELETE CASCADE ON UPDATE CASCADE
    
                        ); """

        if 'displays' not in self.schema.keys():
            self.conn.cursor().execute(displays)
            print("Created budgets table")

        # update schema!
        self.schema = self._get_accounts()

        return

    def create_dashboards(self,):
        dashboards = """ CREATE TABLE IF NOT EXISTS dashboards (
                                    dash_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    dash_desc TEXT NOT NULL,
                                    dash_date DATETIME DEFAULT CURRENT_TIMESTAMP
            
                                ); """

        if 'dashboards' not in self.schema.keys():
            self.conn.cursor().execute(dashboards)
            print("Created dashboards table")
        # update schema!
        self.schema = self._get_accounts()

    def create_displays_dashboards(self,):
        budgets_dashboards = """ CREATE TABLE IF NOT EXISTS displays_dashboardss (
                                    di_id INTEGER,
                                    dash_id INTEGER,
                                    disp_type TEXT NOT NULL,
                                    UNIQUE(di_id, dash_id)
                                    FOREIGN KEY (di_id) REFERENCES displays (di_id) ON DELETE CASCADE ON UPDATE CASCADE,
                                    FOREIGN KEY (dash_id) REFERENCES dashboards (dash_id) ON DELETE CASCADE ON UPDATE CASCADE
            
                                ); """

        if 'budgets_dashboards' not in self.schema.keys():
            self.conn.cursor().execute(budgets_dashboards)
            print("Created budgets_dashboards link table")
        # update schema!
        self.schema = self._get_accounts()

    def create_accounts(self,):
        accounts = """ CREATE TABLE IF NOT EXISTS accounts (
                            acc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            num INTEGER NOT NULL UNIQUE,
                            institution TEXT,
                            desc TEXT,
                            filepath TEXT NOT NULL,
                            source TEXT CHECK(source IN ('file', 'api')),
                            adjust REAL
    
                        ); """

        if 'accounts' not in self.schema.keys():
            self.conn.cursor().execute(accounts)
            print("Created accounts table")
        # update schema!
        self.schema = self._get_accounts()

        return

    def create_crypto(self,):
        crypto = """ CREATE TABLE IF NOT EXISTS crypto (
                        cr_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        desc TEXT NOT NULL,
                        qty REAL NOT NULL,
                        price REAL NOT NULL,
                        total REAL NOT NULL
                        
                    ); """

        if 'crypto' not in self.schema.keys():
            self.conn.cursor().execute(crypto)
            print("Created crypto table")
        # update schema!
        self.schema = self._get_accounts()

        return

    def create_crypto_holdings(self,):
        crypto_holdings = """ CREATE TABLE IF NOT EXISTS crypto_holdings (
                        crh_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        desc TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        parent_chain TEXT,
                        chain_address TEXT
                        
                    ); """

        if 'crypto_holdings' not in self.schema.keys():
            self.conn.cursor().execute(crypto_holdings)
            print("Created crypto_holdings table")
        # update schema!
        self.schema = self._get_accounts()

        return

    def create_qtrade(self,):
        qtrade = """ CREATE TABLE IF NOT EXISTS qtrade (
                        qt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT NOT NULL,
                        symbolId TEXT NOT NULL,
                        openQuantity INTEGER,
                        closeQuantity INTEGER,
                        currentMarketValue REAL NOT NULL,
                        currentPrice REAL NOT NULL,
                        averageEntryPrice REAL NOT NULL,
                        totalCost REAL NOT NULL
                        
                    ); """

        if 'qtrade' not in self.schema.keys():
            self.conn.cursor().execute(qtrade)
            print("Created qtrade table")
        # update schema!
        self.schema = self._get_accounts()

        return

    def create_tags(self,):
        self.create_transactions()
        tags = """ CREATE TABLE IF NOT EXISTS tags (
                            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            desc TEXT NOT NULL UNIQUE
    
                        ); """

        tags_links = """ CREATE TABLE IF NOT EXISTS tags_links (
                            trans_id INTEGER,
                            tag_id INTEGER,
                            UNIQUE(trans_id, tag_id)
                            FOREIGN KEY (trans_id) REFERENCES transactions (trans_id) ON DELETE CASCADE ON UPDATE CASCADE,
                            FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE CASCADE ON UPDATE CASCADE
    
                        ); """

        if 'tags' not in self.schema.keys():
            self.conn.cursor().execute(tags)
            self.conn.cursor().execute(tags_links)
            print("Created tags table")

        # update schema!
        self.schema = self._get_accounts()

        return

    def create_table(self, name):
        """ create default tables used in finance app using default schema set internally
        Args:
        name:   name of table to create(transactions, accounts, categories)

        """

        if name not in self.schema.keys():
            if name == 'transactions':
                self.create_transactions()

            elif name == 'categories':
                self.create_categories()

            elif name == 'accounts':
                self.create_accounts()

            elif name == 'tags':
                self.create_tags()

            elif name == 'crypto':
                self.create_crypto()

            elif name == 'crypto_holdings':
                self.create_crypto_holdings()

            elif name == 'qtrade':
                self.create_qtrade()

            elif name == 'budgets':
                self.create_budgets()
                self.create_dashboards()
                self.create_budgets_dashboards()

            elif name == 'dashboards':
                self.create_budgets()
                self.create_dashboards()
                self.create_budgets_dashboards()

            else:
                pass
        else:
            pass

        return

    def exists(self, table):
        """ Check if table exists"""
        if table in self.schema.keys():
            return True
        else:
            return False


db = FinanceDB()


class Query:
    """ Store query parameters and create queries

        args:
            table:          str of table to perform query operations within
            s_cols:         list of column names as str to be queried
            in_vals:        list of values to be inserted
            up_vals:        list of values to be updated
            w_cols:         list of columns as string to construct query where clauses
            w_conds:        list of operators as strings to use in constructing query where clauses
            w_vals:         list of values to construct where clauses e.g. 'WHERE w_col[1] w_cond[1] w_val[1]'
            o_col:          string column name to be used in order clause
            o_cond:         string denoting order condition, can be 'ASC' or 'DESC', e.g. 'ORDER BY o_col o_cond'
            limit:          string number denoting limit clause, e.g. 'LIMIT limit'
            build_str:      bool indicating if all str properties should be built @ init or later if false
                            allows for addition/modification of query properties post init

        props:
            where_str:      query ready string containing where clauses
            select_str:     query ready string containing select columns
            order_str:      query ready string containing order clause
            limit_str:      query ready string containing limit clause
            values_str:     query ready string containing values for insert
            update_str:     query ready string containing cols/vals for updating
            table:          string table name in which queries operate
            wheres:         list of dictionaries structured [{'col': w_col, 'cond': w_cond, 'va': w_val}]
            o_col:          string column name to order query by
            o_cond:         string condition to order query by, 'ASC' or 'DESC'
            in_vals:        list of values to be inserted - must correspond in order to s_cols
            in_cols:        corresponding list of columns as strings to in_vals
            up_vals:        list of values to be updated - must correspond in order to s_cols
            up_cols:        corresponding list of columns as strings to up_vals
            limit:          string value indicating limit or return query items

        """

    def __init__(self, table, s_cols=None,
                 in_vals=None, in_cols=None,
                 up_vals=None, up_cols=None,
                 w_cols=None, w_conds=None, w_vals=None, w_joins=None,
                 o_col=None, o_cond=None,
                 limit=None,
                 build_str=True):

        # self.db = FinanceDB()
        # initialize properties
        self.table = table
        self.select_str = ""
        self.in_values_str = ""
        self.in_cols_str = ""
        self.update_str = ""
        self.where_str = ""
        self.order_str = ""
        self.limit_str = ""
        self.wheres = []

        if not db.exists(self.table):
            db.create_table(self.table)

        self.w_joins = w_joins
        self.o_col = o_col
        self.o_cond = o_cond
        self.in_vals = in_vals
        self.in_cols = in_cols
        self.up_vals = up_vals
        self.up_cols = up_cols
        self.limit = limit

        # if no s_cols passed then use * (all in sql)
        if s_cols:
            self.s_cols = s_cols
        else:
            # default to all columns instead of *
            self.s_cols = '* '

        if in_vals:
            self.in_vals = self.replace_null(self.in_vals)
            if not in_cols:
                # default to all columns for insert if none passed and in_vals passed
                self.in_cols = db.schema[self.table]

        if up_vals and not up_cols:
            # default to all columns for update if none passed with up_vals
            self.up_cols = db.schema[self.table]

        if w_cols:
            for i in range(0, len(w_cols)):
                where = {}
                # sql will only recognize dates enclosed in apostrophes
                if 'date' in w_cols[i]:
                    w_vals[i] = "'" + w_vals[i] + "'"

                # process all else normally
                where['col'] = w_cols[i]
                where['cond'] = w_conds[i]
                where['val'] = w_vals[i]
                self.wheres.append(where)

        # as long as build str is not false, all query strings will be built
        if build_str:
            self.build_str()

    def build_str(self):
        """ build all query strings given Query properties """
        if not db.exists(self.table):
            db.create_table(self.table)

        # if * in s_cols, select_str is simply * as well
        if '*' not in self.s_cols:
            self.select_str = self._queryize_columns(select=True)
        else:
            self.select_str = '*'

        if self.in_vals:
            self.in_vals = self.replace_null(self.in_vals)
            if not self.in_cols:
                # default to all columns for insert if none passed and in_vals passed
                self.in_cols = db.schema[self.table]
            self.in_values_str = self._queryize_values()
            self.in_cols_str = self._queryize_columns(insert=True)

        if self.up_vals:
            self.update_str = self._queryize_updates(columns=self.up_cols, values=self.up_vals)

        if self.wheres:
            self.where_str = self._queryize_where()

        if self.o_col:
            self.order_str = "ORDER BY " + self.o_col + ' ' + self.o_cond + ' '

        if self.limit:
            self.limit_str = "LIMIT " + self.limit + ' '

        return

    def replace_null(self, p_list):
        """ replace NoneType objects with NULL"""
        p_list = ['NULL' if v is None else v for v in p_list]
        return p_list

    def _queryize_columns(self, select=None, insert=None):
        """create string compatible with injection in sql query from list of strings"""
        col_str = ""
        param = None
        if select:
            param = self.s_cols
        elif insert:
            param = self.in_cols

        if len(param) > 1:
            for col in param:
                if col_str == "":
                    col_str = col_str + col
                else:
                    col_str = col_str + "," + col
        else:
            col_str = param[0]

        return col_str

    def _queryize_values(self,):
        """create string compatible with injection in sql query from list of strings"""
        val_str = ""
        param = self.in_vals

        if len(param) > 1:
            for val in param:
                # replace val with param if injection option not chosen
                if not isinstance(val, str):
                    val = str(val)
                    val_str = val_str + val
                    # remove apostrophe as sql thinks its a string
                    val_str = val_str[0:(-1*(len(val))):] + val_str[(-1*(len(val)))::]
                    val_str += ","

                elif val == 'NULL':
                    val_str = val_str + val + ","
                else:
                    val_str = val_str + "'" + val + "',"
            val_str = val_str[:-1]
        else:
            val_str = param[0]



        return val_str

    def _queryize_where(self):
        """ create queryable string from where properties: WHERE col cond val (AND...) """

        where_str = "WHERE "

        # need to wrap all vals in aprotrophe or might nto work if not already for fucks sake
        for val in self.wheres:
            if val['val'][0] != "'" and val['val'][-1] != "'":
                val['val'] = "'" + val['val'] + "'"

        if len(self.wheres) > 1:
            # w_joins counter
            j = 0
            for i in range(0, len(self.wheres)):
                # if not last where condition then add w_join to prep for next statement
                # w_join is added prior to the where clause, do not add ot first clause
                if i != 0:
                    where_str = where_str + " " + self.w_joins[j] + " "
                    j = j + 1
                else:
                    where_str = where_str + " "

                # like conditions must be wrapped in ''
                if self.wheres[i]['cond'] == 'LIKE':
                    self.wheres[i]['val'] = "'" + self.wheres[i]['val'] + "'"

                where_str = where_str + self.wheres[i]['col'] + ' ' + self.wheres[i]['cond'] + ' ' \
                            + self.wheres[i]['val']

        else:
            if self.wheres[0]['cond'] == 'LIKE':
                self.wheres[0]['val'] = "'" + self.wheres[0]['val'] + "'"
            where_str = where_str + self.wheres[0]['col'] + ' ' + self.wheres[0]['cond'] + ' ' + self.wheres[0]['val']

        return where_str

    def _queryize_updates(self, columns, values):
        """create string compatible with injection in sql query from list of strings"""
        updates_str = ""
        # if string is used as a value it must be wrapped in '
        if isinstance(values, list):

            for i in range(0, len(columns)):
                if updates_str == "":
                    updates_str = columns[i] + " = '" + str(values[i]) + "'"
                else:
                    updates_str = updates_str + ", " + columns[i] + " = '" + str(values[i]) + "'"
        else:
            if isinstance(values, str):
                if values[0] != "'" and values[len(values)] != "'":
                    values = "'" + values + "'"
            updates_str = columns[0] + " = " + values

        return updates_str

    def _query_dict(self, query, table):
        entries = []
        data = db.conn.cursor().execute(query).fetchall()
        keys = db.schema[table]

        for entry in data:
            query_dict = {}
            for i in range(0, len(entry)):
                query_dict[keys[i]] = entry[i]
            entries.append(query_dict)

        return entries

    def build_select(self, build_op='string', function=None):
        # SELECT s_cols FROM table WHERE ORDER LIMIT
        # SELECT function(s_cols) FROM table WHERE ORDER LIMIT

        # data validation for functions and select query argument requirements
        available_functions = ['AVG', 'SUM']
        if function:
            if function not in available_functions:
                print('Function not included, available functions must be one of ' + str(available_functions)[1:-1])
                return
            if len(self.s_cols) != 1 or '*' in self.s_cols:
                print("Function can only be used with single column")
                return

        # always space after latest addition to query - standardize
        query = 'SELECT '

        # build query
        if function:
            query = query + function + '(' + self.select_str + ') '
        elif self.s_cols:
            query = query + self.select_str

        query = query + ' FROM ' + self.table + ' '

        if self.wheres:
            query = query + self.where_str

        if self.o_col:
            query = query + self.order_str

        if self.limit:
            query = query + self.limit_str

        print(query)
        if build_op == 'string':
            return query
        elif build_op == 'dict':
            data = self._query_dict(query=query, table=self.table)
            return data

    def build_insert(self, method='FAIL',):
        # INSERT OR method INTO table (columns,) VALUES (values,)
        query = 'INSERT OR ' + method + ' INTO ' + self.table + \
                ' (' + self.in_cols_str + ') ' + 'VALUES ' + '(' + self.in_values_str + ')'

        print(query)
        return query

    def build_update(self, method='FAIL'):
        # INSERT OR method INTO table (columns,) VALUES (values,)
        query = 'UPDATE OR ' + method + ' ' + self.table + ' SET ' + self.update_str + ' '

        if self.wheres:
            query = query + self.where_str

        print(query)
        return query

    def build_delete(self):
        # TODO DROP TABLE
        # DELETE s_cols FROM table WHERE ORDER LIMIT

        # build query
        query = 'DELETE FROM ' + self.table + ' '

        if self.wheres:
            query = query + self.where_str

        print(query)
        return query
