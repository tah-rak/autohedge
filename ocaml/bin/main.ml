(** AutoHedge OCaml risk CLI.

    Reads a JSON request from --input and writes risk metrics JSON to --output
    (or stdout when --output is omitted).
*)

open Cmdliner

let run input_path output_path simulate =
  try
    let raw = Json_io.read_file input_path in
    let j = Yojson.Basic.from_string raw in
    let metrics = Json_io.compute_from_request_json j in
    let base = Json_io.metrics_to_json metrics in
    let payload =
      if not simulate then base
      else
        let mu =
          match Yojson.Basic.Util.(j |> member "drift" |> to_float_option) with
          | Some x -> x
          | None -> 0.0003
        in
        let sigma = metrics.Types.annualized_volatility /. sqrt 252.0 in
        let mean, p5, p50, p95 =
          Simulation.summarize_paths ~n_paths:500 ~horizon:21 ~mu ~sigma ~seed:42
        in
        match base with
        | `Assoc fields ->
            `Assoc
              (fields
              @ [
                  ( "simulation_21d",
                    `Assoc
                      [
                        ("mean_terminal_wealth", `Float mean);
                        ("p5", `Float p5);
                        ("p50", `Float p50);
                        ("p95", `Float p95);
                      ] );
                ])
        | other -> other
    in
    let text = Yojson.Basic.pretty_to_string payload in
    (match output_path with
    | Some path -> Json_io.write_file path text
    | None -> print_endline text);
    `Ok 0
  with
  | Sys_error msg -> `Error (false, msg)
  | Failure msg -> `Error (false, msg)
  | Yojson.Json_error msg -> `Error (false, "Invalid JSON: " ^ msg)

let input_p =
  let doc = "Path to JSON request file" in
  Arg.(required & opt (some file) None & info [ "i"; "input" ] ~docv:"FILE" ~doc)

let output_p =
  let doc = "Optional output JSON path (default: stdout)" in
  Arg.(value & opt (some string) None & info [ "o"; "output" ] ~docv:"FILE" ~doc)

let simulate_p =
  let doc = "Include a short Monte-Carlo wealth summary" in
  Arg.(value & flag & info [ "simulate" ] ~doc)

let cmd =
  let term = Term.(ret (const run $ input_p $ output_p $ simulate_p)) in
  let info =
    Cmd.info "autohedge-risk"
      ~doc:"Compute AutoHedge portfolio risk metrics from a JSON request"
  in
  Cmd.v info term

let () = exit (Cmd.eval' cmd)
