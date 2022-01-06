from docopt import docopt
import finance_db
import data
import docopt_utility
import copy

# sys.tracebacklimit = 0
# TODO revise usage to make actual sense
# TODO figure out how to limit inputs of arguments instead of parsing options into string after

usage = """

finance_py CLI.

Usage:
    data_driver.py create           ((--a <number> (--TD | --QT | --crypto) (--f | --api) [<description> <adjust>]) | 
                                    ( --t <tag_desc> )... | 
                                    ( --c <cat_desc> )... |
                                    ( --crh <holding_desc> <symbol> [( <parent_chain> <chain_addy> )]))                 
    data_driver.py view <table>     [(--s_col <s_cols>)...
                                    (--w <w_cols> <w_conds> <w_vals> [(--j <w_joins>)])...
                                    (--or <o_col> (--asc | --desc))
                                    (--l <limit>)]                             
    data_driver.py update           (--a (<account> | --all ))
    data_driver.py edit <table>     [(--u <up_cols> <up_vals>)... 
                                    (--w <w_cols> <w_conds> <w_vals> [(--j <w_joins>)])...
                                    (--t <tag_desc>...)]
    data_driver.py split            (--w <w_cols> <w_conds> <w_vals> [(--j <w_joins>)])...
                                    [[ (--p <percent>)  | (--n <new_value>) ] (--u <up_cols> <up_vals>...)]                               
    data_driver.py tag <table>      (--w <w_cols> <w_conds> <w_vals> [(--j <w_joins>)])...
                                    (--t <tag_desc>...)                                  
    data_driver.py delete <table>   [(--w <w_cols> <w_conds> <w_vals> [(--j <w_joins>)])...]
    data_driver.py process
    data_driver.py                  [--help]

Arguments:
    <account>               distinct account number or description
    <adjust>                starting value or adjustment if account data incomplete
    <cat_desc>              new category description
    <chain_addy>            chain/contract address for new crypto holding
    <description>           descriptive identifier or reference for new account
    <holding_desc>          new crypto holding description
    <parent_chain>          name of parent chain for new crypto holding e.g. ethereum for chainlink token
    <number>                new account number, wallet address if crypto
    <s_cols>                columns to be filtered in query/selection
    <symbol>                new crypto holding symbol, must match Yahoo ticker for accurate price information
    <tag_desc>              new tag description
    <w_joins>               keyword string to join where clause to the previous where clause, 'AND' or 'OR'
    <limit>

Options:
    --a                     create a new account  
    --all                   update all accounts
    --api                   new account will use api for updates
    --c                     new category
    --crh                   new crypto holding in blockchain wallet
    --crypto                new blockchain wallet
    --f                     new account will create folder and use files to update  
    --QT                    new Questrade account 
    --s_col                 add selected/filtered columns to query selection
    --t                     new tag
    --TD                    new TD account
    --u                     update accounts            
"""

args = docopt(usage)
# print(args)

docopt_utility.elim_apostrophes(args=args)

# initialize objects to pass to various function calls
query = finance_db.Query(table=args['<table>'],
                         s_cols=args['<s_cols>'],
                         in_vals=None, in_cols=None,
                         up_vals=args['<up_vals>'], up_cols=args['<up_cols>'],
                         w_cols=args['<w_cols>'], w_conds=docopt_utility.process_clause(args), w_vals=args['<w_vals>'], w_joins=args['<w_joins>'],
                         o_col=args['<o_col>'], o_cond=docopt_utility.o_cond(args),
                         limit=args['<limit>'])

db = finance_db.FinanceDB()

if args['delete']:
    db.conn.cursor().execute(query.build_delete())
    db.conn.commit()

if args['process']:
    data.categorize()

if args['edit']:
    # add tags to in_vals and rebuild strings
    if args['<tag_desc>']:
        for tag in args['<tag_desc>']:
            data.tag_entry(db=db, tagged_query=query, tag_param=tag)

    data.edit(db=db, query=query)

if args['split']:
    query.table = 'transactions'
    data.split_transaction(db=db, query=query, percentage=args['<percent>'], amount=args['<new_value>'])

if args['create']:
    if args['--a']:
        # convert source option into string
        source = ""
        if args['--f']:
            source = 'file'
        elif args['--api']:
            source = 'api'

        # convert institution into string
        institution = ""
        if args['--TD']:
            institution = 'TD'
        elif args['--QT']:
            institution = 'QT'
        elif args['--crypto']:
            institution = 'crypto'

        query.table = 'accounts'

        query.in_vals = [None, args['<number>'], institution, args['<description>'], None, source, args['<adjust>']]
        query.build_str()

        comp_columns = copy.deepcopy(query.in_cols)
        comp_columns.pop(0)
        comp_columns.pop(-1)

        data.create_item(db=db, query=query, item_type='account', drop_cond='MIN', drop_method='inside',
                         comp_columns=comp_columns)

    if args['--t']:
        for tag in args['<tag_desc>']:
            query.table = 'tags'
            in_vals = [None, tag]
            query.in_vals = in_vals
            query.build_str()

            data.create_item(db=db, query=query, item_type='tag')

    if args['--c']:
        for category in args['<cat_desc>']:
            query.table = 'categories'
            in_vals = [None, category ]
            query.in_vals = in_vals
            query.build_str()

            data.create_item(db=db, query=query, item_type='category')

    if args['--crh']:
        query.table = 'crypto_holdings'
        in_vals = [None, args['<holding_desc>'], args['<symbol>'], args['<parent_chain>'], args['<chain_addy>']]
        query.in_vals = in_vals
        query.build_str()

        data.create_item(db=db, query=query, item_type='crypto_holding')

if args['tag']:
    for tag in args['<tag_desc>']:
        data.tag_entry(db=db, tagged_query=query, tag_param=tag)

if args['view']:
    if args['<table>'] in db.schema.keys():
        data.view(db=db, query=query)
    else:
        print("Table does not exist")

if args['--help']:
    print(usage)

if args['update']:
    if args['--a']:
        if args['<account>']:
            data.update_account(db=db, account=args['<account>'])

        elif args['--all']:
            accounts = db.conn.cursor().execute("SELECT num FROM accounts").fetchall()

            for account in accounts:

                data.update_account(db=db, account=account[0])
