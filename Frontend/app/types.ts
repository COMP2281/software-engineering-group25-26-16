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

export interface FileStats {
  id: number;
  filename: string;
  warning_count: number;
  diagnostics_ran: boolean;
}
