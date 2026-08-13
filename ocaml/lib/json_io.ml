(** JSON read/write for interop with the Python orchestration layer. *)

open Types
open Yojson.Basic
open Yojson.Basic.Util

let holding_of_json j =
  {
    symbol = j |> member "symbol" |> to_string;
    asset_class =
      j |> member "asset_class" |> to_string |> asset_class_of_string;
    sector = j |> member "sector" |> to_string_option |> Option.value ~default:"unknown";
    weight = j |> member "weight" |> to_float;
  }

let portfolio_of_json j =
  {
    name = j |> member "name" |> to_string;
    currency =
      j |> member "currency" |> to_string_option |> Option.value ~default:"USD";
    cash_weight =
      j |> member "cash_weight" |> to_float_option |> Option.value ~default:0.0;
    holdings =
      j |> member "holdings" |> to_list |> List.map holding_of_json;
  }

let float_list_of_json = function
  | `List xs -> List.map to_float xs
  | _ -> []

let returns_map_of_json j =
  j |> to_assoc
  |> List.map (fun (sym, series) -> (sym, float_list_of_json series))

let metrics_to_json (m : risk_metrics) =
  `Assoc
    [
      ("annualized_volatility", `Float m.annualized_volatility);
      ("var_95", `Float m.var_95);
      ("cvar_95", `Float m.cvar_95);
      ("max_drawdown", `Float m.max_drawdown);
      ("sharpe_proxy", `Float m.sharpe_proxy);
      ("concentration_hhi", `Float m.concentration_hhi);
      ("top_weight", `Float m.top_weight);
      ("avg_correlation", `Float m.avg_correlation);
      ("equity_exposure", `Float m.equity_exposure);
      ("beta_proxy", `Float m.beta_proxy);
      ("engine", `String "ocaml");
    ]

let read_file path =
  let ic = open_in path in
  let len = in_channel_length ic in
  let s = really_input_string ic len in
  close_in ic;
  s

let write_file path s =
  let oc = open_out path in
  output_string oc s;
  close_out oc

let compute_from_request_json j =
  let portfolio = j |> member "portfolio" |> portfolio_of_json in
  let returns_by_symbol =
    j |> member "returns_by_symbol" |> returns_map_of_json
  in
  let benchmark =
    match j |> member "benchmark_returns" with
    | `Null ->
        (match List.assoc_opt "SPY" returns_by_symbol with
        | Some xs -> xs
        | None -> (
            match returns_by_symbol with
            | (_, xs) :: _ -> xs
            | [] -> []))
    | other -> float_list_of_json other
  in
  let annualization =
    j |> member "annualization" |> to_float_option |> Option.value ~default:252.0
  in
  let confidence =
    j |> member "confidence" |> to_float_option |> Option.value ~default:0.95
  in
  Risk.compute ~portfolio ~returns_by_symbol ~benchmark_returns:benchmark
    ~annualization ~confidence ()
