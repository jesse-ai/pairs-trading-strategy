from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class PairsTrading(Strategy):
    @property
    def c1(self):
        return utils.prices_to_returns(
            self.get_candles(self.exchange, self.routes[0].symbol, self.timeframe)[:, 2][-200:]
        )
    
    @property
    def c2(self):
        return utils.prices_to_returns(
            self.get_candles(self.exchange, self.routes[1].symbol, self.timeframe)[:, 2][-200:]
        )
    
    @property
    def z_score(self):
        spread = self.c1[1:] - self.c2[1:]
        z_scores = utils.z_score(spread)
        return z_scores[-1]
    
    def before(self) -> None:
        if self.index == 0:
            self.shared_vars["s1-position"] = 0
            self.shared_vars["s2-position"] = 0
        
        # every 24 hours
        if self.index == 0 or self.index % (24 * 60 / utils.timeframe_to_one_minutes(self.timeframe)) == 0:
            is_cointegrated = utils.are_cointegrated(self.c1[1:], self.c2[1:])
            if not is_cointegrated:
                self.shared_vars["s1-position"] = 0
                self.shared_vars["s2-position"] = 0

        z_scores = self.z_score
        if self.is_close and z_scores < -1.2:
            self.shared_vars["s1-position"] = 1
            self.shared_vars["s2-position"] = -1
            self._set_proper_margin_per_route()
        elif self.is_long and z_scores > 0:
            self.shared_vars["s1-position"] = 0
            self.shared_vars["s2-position"] = 0
        elif self.is_short and z_scores < 0:
            self.shared_vars["s1-position"] = 0
            self.shared_vars["s2-position"] = 0
        elif self.is_close and z_scores > 1.2:
            self.shared_vars["s1-position"] = -1
            self.shared_vars["s2-position"] = 1
            self._set_proper_margin_per_route()
            
    def _set_proper_margin_per_route(self):
        _, beta = utils.calculate_alpha_beta(self.c1[1:], self.c2[1:])
        self.shared_vars["margin1"] = self.available_margin * (1 / (1 + beta))
        self.shared_vars["margin2"] = self.available_margin * (beta / (1 + beta))

    def should_long(self) -> bool:
        return self.shared_vars["s1-position"] == 1

    def should_short(self) -> bool:
        return self.shared_vars["s1-position"] == -1
        
    def go_long(self):
        qty = utils.size_to_qty(self.shared_vars["margin1"], self.price, fee_rate=self.fee_rate)
        self.buy = qty, self.price

    def go_short(self):
        qty = utils.size_to_qty(self.shared_vars["margin1"], self.price, fee_rate=self.fee_rate)
        self.sell = qty, self.price

    def update_position(self):
        if self.shared_vars["s1-position"] == 0:
            self.liquidate()
