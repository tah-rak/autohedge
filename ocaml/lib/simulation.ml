(** Lightweight Monte-Carlo style path summary used by the CLI. *)

let summarize_paths ~n_paths ~horizon ~mu ~sigma ~seed =
  let state = ref seed in
  let rand () =
    (* Minimal LCG for reproducible local demos (no external RNG dep). *)
    state := (1664525 * !state + 1013904223) land 0x7fffffff;
    float_of_int !state /. float_of_int 0x7fffffff
  in
  let box_muller () =
    let u1 = max 1e-12 (rand ()) in
    let u2 = rand () in
    sqrt (-2.0 *. log u1) *. cos (2.0 *. Float.pi *. u2)
  in
  let terminal = ref [] in
  for _ = 1 to n_paths do
    let w = ref 1.0 in
    for _d = 1 to horizon do
      let z = box_muller () in
      let r = mu +. (sigma *. z) in
      w := !w *. (1.0 +. r)
    done;
    terminal := !w :: !terminal
  done;
  let xs = List.sort compare !terminal in
  let mean = Market.mean xs in
  let p5 = Market.percentile_sorted xs 0.05 in
  let p50 = Market.percentile_sorted xs 0.50 in
  let p95 = Market.percentile_sorted xs 0.95 in
  (mean, p5, p50, p95)
