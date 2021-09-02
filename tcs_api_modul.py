import pandas as pd
import tinvest
import streamlit as st
import json


@st.cache
def get_positions_by_acc(account_id, client):
    positions = client.get_portfolio(account_id)  # get portfolio by broker_account_id
    df_positions = pd.DataFrame(columns=["Name", "Ticker", "Balance", "Currency", "Price"])

    for position in positions.payload.positions:
        df_positions = df_positions.append({"Name": position.name, "Ticker": position.ticker,
                                            "Balance": position.balance,
                                            "Currency": position.average_position_price.currency.value,
                                            "Price": position.average_position_price.value},
                                           ignore_index=True)
    return df_positions


def split_operations_by_type(operations, dict_type):
    for i in range(len(operations)):
        for op_type in dict_type.keys():
            #st.write(op_type)
            #st.write(json.loads(operations[i].json()))
            if operations[i].operation_type == op_type:
                dict_type.get(op_type).append(operations[i])

    return dict_type


def split_buy_fifo(sell_counter, df_fifo_table, sell_date, sell_price, sell_quantity):
    new_index_part_1 = [i for i in range(0, sell_counter + 1)]
    new_index_part_2 = [n for n in range(sell_counter + 2, df_fifo_table.shape[0] + 1)]
    new_index_part_1.extend(new_index_part_2)

    # df_fifo_table = df_fifo_table.reindex(new_index_part_1)  # reindex dataframe
    df_fifo_table.index = new_index_part_1

    df_fifo_table.loc[sell_counter + 1] = pd.Series(df_fifo_table.loc[sell_counter])

    df_fifo_table = df_fifo_table.sort_index()

    df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
    df_fifo_table.at[sell_counter, 'sell_date'] = sell_date
    df_fifo_table.at[sell_counter, 'sell_price'] = sell_price

    df_fifo_table.at[sell_counter, 'sell_quantity'] = sell_quantity

    df_fifo_table.at[sell_counter + 1, 'buy_quantity'] = df_fifo_table.at[sell_counter, 'buy_quantity'] - df_fifo_table.at[sell_counter, 'sell_quantity']  # residual to buy
    df_fifo_table.at[sell_counter, 'buy_quantity'] = df_fifo_table.at[sell_counter, 'sell_quantity']  # change buy_quantity = sell_quantity

    return df_fifo_table



