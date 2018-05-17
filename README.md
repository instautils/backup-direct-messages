# backup-direct-messages
An easy way to backup all of your Instagram direct messages in an Instagram direct thread.

### Only Backup

This program will save all of messages in `output/dump_file.csv` directory and download all of media in `output`.

```bash
  python main.py -u <username> -p <password> -t <thread-title>
```

CSV headers are :

1. UserID
2. Message
3. ItemID
4. Timestamp

### Backup and clean

```bash
  python main.py -u <username> -p <password> -t <thread-title> --remove True
```

##### What is <thread-title> ?

Each one of threads has title.
When you are texting to your friend in Instagram direct , You will see your friend's username in title (header). That is `thread-title`.

##### Debug mode

Use `--debug True` to see logs in stdout. Use `--log-file` to write logs into specific file.
