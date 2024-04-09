import json
from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict

class Trader:
    def __init__(self):
        print("Initializing trader...")
        self.base_window_size = 5  # Base window size for moving averages
        # Position limits for each product
        self.position_limits = {'AMETHYSTS': 20, 'STARFRUIT': 20}
        print(f"Position limits set: {self.position_limits}")

    def calculate_moving_average(self, prices: List[float], window_size: int) -> float:
        if len(prices) == 0:
            print("Price list is empty, returning 0")
            return 0
        window_size = min(window_size, len(prices))
        average = sum(prices[-window_size:]) / window_size
        print(f"Calculated moving average with window size {window_size}: {average}")
        return average

    def run(self, state: TradingState):
        print("Starting trading run...")
        print(f"Trader data from previous run: {state.traderData}")
        print(f"Current observations: {state.observations}")

        result = {}
        trader_data = {}

        try:
            trader_data = json.loads(state.traderData) if state.traderData else {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        for product in state.order_depths:
            try:
                print(f"Processing product: {product}")
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                if product not in trader_data:
                    trader_data[product] = {'price_history': [], 'support': None, 'resistance': None}

                price_history = trader_data[product]['price_history']

                # Use current position from TradingState
                current_position = state.position.get(product, 0)

                if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

                    mid_price = (best_ask + best_bid) / 2.0
                    price_history.append(mid_price)

                    stma = self.calculate_moving_average(price_history, min(len(price_history), 2))
                    ltma = self.calculate_moving_average(price_history, min(len(price_history), self.base_window_size))
                    trend = 'upward' if stma > ltma else 'downward' if stma < ltma else 'sideways'

                    # Order placement considering current position and position limits
                    if trend == 'upward' and current_position < self.position_limits[product]:
                        order_quantity = -min(best_ask_amount, self.position_limits[product] - current_position)
                        orders.append(Order(product, best_ask, order_quantity))

                    elif trend == 'downward' and current_position > -self.position_limits[product]:
                        order_quantity = min(best_bid_amount, current_position + self.position_limits[product])
                        orders.append(Order(product, best_bid, order_quantity))

                result[product] = orders
                trader_data[product]['price_history'] = price_history

            except Exception as e:
                print(f"Error processing product {product}: {e}")

        try:
            trader_data_str = json.dumps(trader_data)
        except TypeError as e:
            print(f"Error serializing trader data: {e}")
            trader_data_str = "{}"

        conversions = None  # Replace with actual logic if needed
        return result, conversions, trader_data_str
