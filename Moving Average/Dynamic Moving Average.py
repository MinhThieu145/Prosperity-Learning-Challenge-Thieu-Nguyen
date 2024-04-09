import json
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

class Trader:
    def __init__(self):
        self.base_window_size = 5  # Base window size

    def calculate_moving_average(self, prices: List[float]) -> float:
        if len(prices) == 0:
            return 0
        return sum(prices) / len(prices)

    def calculate_volatility(self, prices: List[float]) -> float:
        if len(prices) < 2:
            return 0
        differences = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
        return sum(differences) / len(differences)

    def update_price_history(self, price: float, price_history: List[float], window_size: int) -> List[float]:
        price_history.append(price)
        if len(price_history) > window_size:
            price_history = price_history[-window_size:]
        return price_history

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {'AMETHYSTS': [], 'STARFRUIT': []}

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
                price_history.append(float(best_ask))
                volatility = self.calculate_volatility(price_history)
                # Adjust the window size based on volatility
                window_size = max(int(self.base_window_size * (1 + volatility)), 1)
                price_history = self.update_price_history(float(best_ask), price_history, window_size)
                moving_average = self.calculate_moving_average(price_history[-window_size:])

                if float(best_ask) < moving_average:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if not price_history or price_history[-1] != float(best_bid):
                    price_history.append(float(best_bid))
                volatility = self.calculate_volatility(price_history)
                # Adjust the window size based on volatility
                window_size = max(int(self.base_window_size * (1 + volatility)), 1)
                price_history = self.update_price_history(float(best_bid), price_history, window_size)
                moving_average = self.calculate_moving_average(price_history[-window_size:])

                if float(best_bid) > moving_average:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))

            result[product] = orders
            trader_data[product] = price_history

        # Serialize trader_data to JSON string before returning
        trader_data_str = json.dumps(trader_data)

        conversions = 1
        return result, conversions, trader_data_str
