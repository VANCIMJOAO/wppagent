#!/bin/bash
# Script de monitoramento da replicação

check_replication_status() {
    echo "📊 STATUS DA REPLICAÇÃO"
    echo "======================"
    
    # Status no Primary
    echo "PRIMARY SERVER:"
    sudo -u postgres psql -c "
        SELECT 
            client_addr,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            write_lag,
            flush_lag,
            replay_lag
        FROM pg_stat_replication;
    "
    
    # Lag da replicação
    echo ""
    echo "REPLICATION LAG:"
    sudo -u postgres psql -c "
        SELECT 
            CASE 
                WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() 
                THEN 0 
                ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp()) 
            END AS lag_seconds;
    "
}

check_replica_status() {
    echo "📊 STATUS DO REPLICA"
    echo "==================="
    
    sudo -u postgres psql -c "
        SELECT 
            pg_is_in_recovery() as is_replica,
            pg_last_wal_receive_lsn() as received_lsn,
            pg_last_wal_replay_lsn() as replayed_lsn,
            pg_last_xact_replay_timestamp() as last_replay;
    "
}

case "$1" in
    "primary")
        check_replication_status
        ;;
    "replica")
        check_replica_status
        ;;
    *)
        echo "Uso: $0 {primary|replica}"
        ;;
esac
