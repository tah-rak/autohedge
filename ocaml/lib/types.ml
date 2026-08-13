(** Core domain types for AutoHedge risk calculations. *)

type asset_class =
  | Equity
  | Etf
  | Bond
  | Commodity
  | Crypto
  | Cash
  | Other

type holding = {
  symbol : string;
  asset_class : asset_class;
  sector : string;
  weight : float;
}

type portfolio = {
  name : string;
  currency : string;
  cash_weight : float;
  holdings : holding list;
}

type risk_metrics = {
  annualized_volatility : float;
  var_95 : float;
  cvar_95 : float;
  max_drawdown : float;
  sharpe_proxy : float;
  concentration_hhi : float;
  top_weight : float;
  avg_correlation : float;
  equity_exposure : float;
  beta_proxy : float;
}

let asset_class_of_string s =
  match String.lowercase_ascii s with
  | "equity" -> Equity
  | "etf" -> Etf
  | "bond" -> Bond
  | "commodity" -> Commodity
  | "crypto" -> Crypto
  | "cash" -> Cash
  | _ -> Other

let asset_class_to_string = function
  | Equity -> "equity"
  | Etf -> "etf"
  | Bond -> "bond"
  | Commodity -> "commodity"
  | Crypto -> "crypto"
  | Cash -> "cash"
  | Other -> "other"
