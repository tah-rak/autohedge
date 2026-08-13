(** Risk metrics: volatility, VaR/CVaR, drawdown, correlation, beta proxy. *)

open Types

let portfolio_returns (weights : (string * float) list)
    (returns_by_symbol : (string * float list) list) =
  match returns_by_symbol with
  | [] -> []
  | (_, first) :: _ ->
      let n = List.length first in
      let get_ret sym i =
        match List.assoc_opt sym returns_by_symbol with
        | None -> 0.0
        | Some xs -> (try List.nth xs i with _ -> 0.0)
      in
      let rec build i acc =
        if i >= n then List.rev acc
        else
          let r =
            List.fold_left
              (fun s (sym, w) -> s +. (w *. get_ret sym i))
              0.0 weights
          in
          build (i + 1) (r :: acc)
      in
      build 0 []

let annualized_vol returns annualization =
  Market.stddev returns *. sqrt annualization

let historical_var returns confidence =
  let sorted = List.sort compare returns in
  let p = 1.0 -. confidence in
  ~-.(Market.percentile_sorted sorted p)

let historical_cvar returns confidence =
  let sorted = List.sort compare returns in
  let n = List.length sorted in
  if n = 0 then 0.0
  else
    let cutoff = 1.0 -. confidence in
    let k = max 1 (int_of_float (floor (cutoff *. float_of_int n))) in
    let rec take i acc = function
      | [] -> List.rev acc
      | _ when i >= k -> List.rev acc
      | x :: rest -> take (i + 1) (x :: acc) rest
    in
    let tail = take 0 [] sorted in
    let mu = Market.mean tail in
    ~-.mu

let sharpe_proxy returns annualization risk_free =
  let mu = Market.mean returns *. annualization in
  let vol = annualized_vol returns annualization in
  if vol <= 1e-12 then 0.0 else (mu -. risk_free) /. vol

let average_pairwise_correlation (returns_by_symbol : (string * float list) list)
    =
  let series = List.map snd returns_by_symbol in
  let n = List.length series in
  if n < 2 then 0.0
  else
    let rec pairs i j acc count =
      if i >= n then (acc, count)
      else if j >= n then pairs (i + 1) (i + 2) acc count
      else
        let c = Market.correlation (List.nth series i) (List.nth series j) in
        pairs i (j + 1) (acc +. c) (count + 1)
    in
    let sum, count = pairs 0 1 0.0 0 in
    if count = 0 then 0.0 else sum /. float_of_int count

let beta_proxy portfolio_returns benchmark_returns =
  let var_b = Market.variance benchmark_returns in
  if var_b <= 1e-18 then 1.0
  else Market.covariance portfolio_returns benchmark_returns /. var_b

let wealth_path returns =
  let rec aux w acc = function
    | [] -> List.rev acc
    | r :: rest ->
        let w' = w *. (1.0 +. r) in
        aux w' (w' :: acc) rest
  in
  aux 1.0 [ 1.0 ] returns

let compute ~(portfolio : portfolio) ~returns_by_symbol ~benchmark_returns
    ?(annualization = 252.0) ?(risk_free = 0.02) ?(confidence = 0.95) () =
  let _ = Portfolio.validate portfolio in
  let weights =
    List.map (fun (h : holding) -> (h.symbol, h.weight)) portfolio.holdings
  in
  let prets = portfolio_returns weights returns_by_symbol in
  let prices = wealth_path prets in
  {
    annualized_volatility = annualized_vol prets annualization;
    var_95 = historical_var prets confidence;
    cvar_95 = historical_cvar prets confidence;
    max_drawdown = Market.max_drawdown prices;
    sharpe_proxy = sharpe_proxy prets annualization risk_free;
    concentration_hhi = Portfolio.herfindahl portfolio;
    top_weight = Portfolio.top_weight portfolio;
    avg_correlation = average_pairwise_correlation returns_by_symbol;
    equity_exposure = Portfolio.equity_like_exposure portfolio;
    beta_proxy = beta_proxy prets benchmark_returns;
  }
