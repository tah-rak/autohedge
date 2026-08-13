(** Market series utilities used by the risk engine. *)

let mean xs =
  match xs with
  | [] -> 0.0
  | _ ->
      let n = float_of_int (List.length xs) in
      List.fold_left ( +. ) 0.0 xs /. n

let variance xs =
  match xs with
  | [] | [ _ ] -> 0.0
  | _ ->
      let mu = mean xs in
      let n = float_of_int (List.length xs) in
      let ss =
        List.fold_left (fun acc x -> let d = x -. mu in acc +. (d *. d)) 0.0 xs
      in
      ss /. (n -. 1.0)

let stddev xs = sqrt (variance xs)

let returns_from_prices prices =
  let rec aux prev acc = function
    | [] -> List.rev acc
    | p :: rest ->
        let r = if prev <= 0.0 then 0.0 else (p /. prev) -. 1.0 in
        aux p (r :: acc) rest
  in
  match prices with
  | [] | [ _ ] -> []
  | p0 :: rest -> aux p0 [] rest

let take n xs =
  let rec aux i acc = function
    | [] -> List.rev acc
    | _ when i >= n -> List.rev acc
    | x :: rest -> aux (i + 1) (x :: acc) rest
  in
  aux 0 [] xs

let covariance xs ys =
  let n = min (List.length xs) (List.length ys) in
  if n < 2 then 0.0
  else
    let xs = take n xs in
    let ys = take n ys in
    let mx = mean xs in
    let my = mean ys in
    let s =
      List.fold_left2
        (fun acc x y -> acc +. ((x -. mx) *. (y -. my)))
        0.0 xs ys
    in
    s /. float_of_int (n - 1)

let correlation xs ys =
  let sx = stddev xs in
  let sy = stddev ys in
  if sx <= 1e-12 || sy <= 1e-12 then 0.0 else covariance xs ys /. (sx *. sy)

let percentile_sorted sorted_asc p =
  let n = List.length sorted_asc in
  if n = 0 then 0.0
  else
    let idx =
      int_of_float (floor (p *. float_of_int (n - 1))) |> max 0 |> min (n - 1)
    in
    List.nth sorted_asc idx

let max_drawdown prices =
  let rec aux peak mdd = function
    | [] -> mdd
    | p :: rest ->
        let peak' = max peak p in
        let dd = if peak' <= 0.0 then 0.0 else (peak' -. p) /. peak' in
        aux peak' (max mdd dd) rest
  in
  match prices with
  | [] -> 0.0
  | p0 :: rest -> aux p0 0.0 (p0 :: rest)
