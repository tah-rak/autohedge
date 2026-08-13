(** Portfolio helpers: weights, exposures, concentration. *)

open Types

let total_invested_weight (p : portfolio) =
  List.fold_left (fun acc h -> acc +. h.weight) 0.0 p.holdings

let validate (p : portfolio) =
  let invested = total_invested_weight p in
  let total = invested +. p.cash_weight in
  if abs_float (total -. 1.0) > 0.02 then
    failwith
      (Printf.sprintf
         "Portfolio weights must sum to ~1.0 (got %.4f including cash)" total);
  p

let herfindahl (p : portfolio) =
  List.fold_left (fun acc h -> acc +. (h.weight *. h.weight)) 0.0 p.holdings

let top_weight (p : portfolio) =
  match p.holdings with
  | [] -> 0.0
  | hs -> List.fold_left (fun m h -> max m h.weight) 0.0 hs

let exposure_by_asset_class (p : portfolio) (ac : asset_class) =
  List.fold_left
    (fun acc h -> if h.asset_class = ac then acc +. h.weight else acc)
    0.0 p.holdings

let equity_like_exposure (p : portfolio) =
  exposure_by_asset_class p Equity +. exposure_by_asset_class p Etf

let sector_exposures (p : portfolio) =
  let tbl = Hashtbl.create 16 in
  List.iter
    (fun h ->
      let prev = try Hashtbl.find tbl h.sector with Not_found -> 0.0 in
      Hashtbl.replace tbl h.sector (prev +. h.weight))
    p.holdings;
  Hashtbl.fold (fun k v acc -> (k, v) :: acc) tbl []
