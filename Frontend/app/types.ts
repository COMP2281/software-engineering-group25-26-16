export interface Warning {
  run_time: number;
  severity: string;
  type: string;
  message: string;
}

export interface File {
  user_id: number;
  filename: string;
  id: number;
}
