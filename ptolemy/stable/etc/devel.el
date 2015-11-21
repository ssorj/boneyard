(setq devel-home (getenv "DEVEL_HOME"))

(if devel-home
    (progn
      (shell "dev")
      (setq tags-file-name (concat devel-home "/etc/devel.tags"))
      (setq grep-command "find-code | xargs fgrep -n ")
      (setq auto-mode-alist
            (cons '("\\.script$" . sh-mode) auto-mode-alist)))
  (display-warning 'devel
                   "Environment variable DEVEL_HOME not set" :error))
