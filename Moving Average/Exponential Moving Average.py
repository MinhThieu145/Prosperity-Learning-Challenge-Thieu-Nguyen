import json
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

class Trader:
    def __init__(self):
        self.window_size = 5  # This represents the period for EMA calculation
        self.smoothing = 2  # Smoothing factor commonly set to 2 for EMA

    def calculate_ema(self, price: float, previous_ema: float) -> float:
        alpha = self.smoothing / (1 + self.window_size)
        return (price * alpha) + (previous_ema * (1 - alpha))

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        trader_data = json.loads(state.traderData) if state.traderData else {}

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders = []

            # Initialize or update EMA for the product
            if product not in trader_data:
                trader_data[product] = {"ema": 0, "initialized": False}
            ema_data = trader_data[product]

            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if ema_data["initialized"]:
                    ema = self.calculate_ema(float(best_ask), ema_data["ema"])
                else:
                    ema = float(best_ask)  # Initialize EMA with the first price
                    ema_data["initialized"] = True

                if float(best_ask) < ema:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
                ema_data["ema"] = ema

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if ema_data["initialized"]:
                    ema = self.calculate_ema(float(best_bid), ema_data["ema"])
                else:
                    ema = float(best_bid)  # Initialize EMA with the first price
                    ema_data["initialized"] = True

                if float(best_bid) > ema:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
                ema_data["ema"] = ema

            result[product] = orders
            trader_data[product] = ema_data

        # Serialize trader_data to JSON string before returning
        # trader_data_str = json.dumps(trader_data)

        conversions = 1
        return result, conversions, trader_data
