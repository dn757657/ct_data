from qtrade import Questrade
import pathlib
import db_utility

fipy_fp = pathlib.Path(__file__).absolute().parent.parent
src_path = fipy_fp.joinpath('src')
yaml_path = src_path.joinpath('access_token.yml')

def qtrade_connect():
    print(yaml_path)
    try:
        # access_code = 'hJxEWwStLWDPAx397CYGXc93AtQEeAa10'
        # qtrade = Questrade(access_code=access_code)
        qtrade = Questrade(token_yaml=yaml_path)
        qtrade.refresh_access_token(from_yaml=True)
    except:
        # qtrade = Questrade(token_yaml=yaml_path)
        # qtrade.refresh_access_token(from_yaml=True)
        access_code = input("please input Questrade API Access token ")
        qtrade = Questrade(access_code=access_code)

    return qtrade


def update_qpositions(db, account_id):
    if not db.exists('qtrade'):
        db.create_table('qtrade')

    qtrade = qtrade_connect()
    positions = qtrade.get_account_positions(account_id=account_id)
    for pos in positions:
        update = {key: None for key in db.schema['qtrade']}
        for key in update.keys():
            # db table column names are same as default dictionary names for properties in position
            # need to eliminate params that are in positions dictionaries but not in db qtrade table
            if key in pos.keys():
                update[key] = pos[key]

        update.pop('date')
        update_cols = list(update.keys())
        update_vals = list(update.values())

        query = db_utility.Query(table='qtrade',
                                 in_vals=update_vals, in_cols=update_cols, )

        # query = db.insert(table='qtrade', columns=update_cols, values=update_vals)
        db.conn.cursor().execute(query.build_insert())
        db.conn.commit()
