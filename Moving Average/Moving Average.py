import json
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

class Trader:
    def __init__(self):
        self.window_size = 5

    def calculate_moving_average(self, prices: List[float]) -> float:
        if len(prices) == 0:
            return 0
        return sum(prices) / len(prices)
    
    def update_price_history(self, price: float, price_history: List[float]) -> List[float]:
        if len(price_history) < self.window_size:
            price_history.append(price)
        else:
            price_history.pop(0)
            price_history.append(price)
        return price_history

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        # Deserialize traderData from JSON string to dictionary
        trader_data = json.loads(state.traderData) if state.traderData else {}

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # Initialize or update price history for the product
            if product not in trader_data:
                trader_data[product] = []
            price_history = trader_data[product]

            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                price_history = self.update_price_history(float(best_ask), price_history)
                moving_average = self.calculate_moving_average(price_history)

                if float(best_ask) < moving_average:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if len(price_history) == 0 or price_history[-1] != float(best_bid):
                    price_history = self.update_price_history(float(best_bid), price_history)
                moving_average = self.calculate_moving_average(price_history)

                if float(best_bid) > moving_average:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))

            result[product] = orders
            trader_data[product] = price_history

        # Serialize trader_data to JSON string before returning
        trader_data_str = json.dumps(trader_data)

        conversions = 1
        return result, conversions, trader_data_str
