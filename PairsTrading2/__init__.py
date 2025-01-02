from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class PairsTrading2(Strategy):
    def should_long(self) -> bool:
        return self.shared_vars["s2-position"] == 1

    def should_short(self) -> bool:
        return self.shared_vars["s2-position"] == -1
        
    def go_long(self):
        qty = utils.size_to_qty(self.shared_vars["margin2"], self.price, fee_rate=self.fee_rate)
        self.buy = qty, self.price
        
    def go_short(self):
        qty = utils.size_to_qty(self.shared_vars["margin2"], self.price, fee_rate=self.fee_rate)
        self.sell = qty, self.price

    def update_position(self):
        if self.shared_vars["s2-position"] == 0:
            self.liquidate()
