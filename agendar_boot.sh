#!/bin/bash
# Limpa o agendamento anterior do RTC
sudo rtcwake -m disable 2>/dev/null || echo 0 > /sys/class/rtc/rtc0/wakealarm 2>/dev/null || true
sleep 1

# ============================================
# CONFIGURAÇÃO
# Horário (em horário LOCAL) que o PC deve ligar
# 0 a esquerda é interpretado como octal e gera erro. Exemplo: 09 (errado); 9 (certo). 00 (errado); 0 certo.
# ============================================
HORA_LOCAL_AGENDADA=8        # Hora local (0-23)
MINUTO_LOCAL_AGENDADO=57     # Minuto (0-59)

# ============================================
# LÓGICA
# Converte o horário local desejado para um timestamp UTC real
# (via epoch, evitando a armadilha do "date -u -d", que reinterpreta
# em vez de converter).
# ============================================
HORARIO_LOCAL_HOJE="$(date +%Y-%m-%d) $(printf '%02d:%02d' $HORA_LOCAL_AGENDADA $MINUTO_LOCAL_AGENDADO)"
EPOCH_ALVO_LOCAL=$(date -d "$HORARIO_LOCAL_HOJE" +%s)
HORA_UTC_AGENDADA=$((10#$(date -u -d @$EPOCH_ALVO_LOCAL +%H)))
MINUTO_UTC_AGENDADO=$((10#$(date -u -d @$EPOCH_ALVO_LOCAL +%M)))

# Hora atual em UTC, em minutos
HORA_ATUAL=$(date -u +%H)
MINUTO_ATUAL=$(date -u +%M)
MINUTOS_ATUAL=$(( (10#$HORA_ATUAL * 60) + 10#$MINUTO_ATUAL ))

# Horário alvo (já em UTC), em minutos
MINUTOS_ALVO=$(( (10#$HORA_UTC_AGENDADA * 60) + 10#$MINUTO_UTC_AGENDADO ))

# Se já passou do horário hoje, agenda para amanhã
if [ $MINUTOS_ATUAL -ge $MINUTOS_ALVO ]; then
    DATA=$(date -u -d "tomorrow" +%Y-%m-%d)
else
    DATA=$(date -u -d "today" +%Y-%m-%d)
fi

# ============================================
# AJUSTE DE FIM DE SEMANA
# Se o próximo boot cair em sábado, adianta 2 dias (cai na segunda).
# Se cair em domingo, adianta 1 dia (cai na segunda).
# ============================================
DIA_SEMANA_ALVO=$(date -u -d "$DATA" +%u)  # 1=segunda ... 6=sábado, 7=domingo
if [ "$DIA_SEMANA_ALVO" -eq 6 ]; then
    DATA=$(date -u -d "$DATA +2 days" +%Y-%m-%d)
elif [ "$DIA_SEMANA_ALVO" -eq 7 ]; then
    DATA=$(date -u -d "$DATA +1 day" +%Y-%m-%d)
fi

# Monta a data/hora alvo e converte para timestamp epoch (sempre UTC real)
HORARIO_BOOT_UTC="$DATA $(printf '%02d:%02d' $HORA_UTC_AGENDADA $MINUTO_UTC_AGENDADO) UTC"
TIMESTAMP_UTC=$(date -d "$HORARIO_BOOT_UTC" +%s)

# DEBUG
#echo "=========================================="
#echo "DEBUG:"
#echo "  Horário local pedido: $HORARIO_LOCAL_HOJE"
#echo "  Horário UTC calculado: $(printf '%02d:%02d' $HORA_UTC_AGENDADA $MINUTO_UTC_AGENDADO)"
#echo "  Data alvo: $DATA"
#echo "  Timestamp: $TIMESTAMP_UTC"
#echo "=========================================="

# ============================================
# GRAVAÇÃO: usa o rtcwake em vez de escrever direto no sysfs.
# O rtcwake (utilitário padrão do util-linux) lê o /etc/adjtime e faz
# sozinho a tradução correta entre UTC e horário local do RTC físico —
# isso resolve, de forma madura e testada, o problema que fazia a
# gravação manual funcionar em algumas placas e falhar em outras.
# "-m no" só grava o alarme, sem suspender/desligar a máquina agora.
# ============================================
sudo rtcwake -m no -a -t "$TIMESTAMP_UTC"
RC=$?
sleep 1

VALOR_GRAVADO=$(cat /sys/class/rtc/rtc0/wakealarm 2>/dev/null)
if [ $RC -eq 0 ] && [ -n "$VALOR_GRAVADO" ]; then
    PROXIMA_DATA_UTC=$(date -u -d @$TIMESTAMP_UTC "+%d/%m/%Y às %H:%M:%S UTC")
    PROXIMA_DATA_LOCAL=$(date -d @$TIMESTAMP_UTC "+%d/%m/%Y às %H:%M:%S %Z")
    {
        echo ""
        echo "=========================================="
        echo "  ✓ PRÓXIMO BOOT AGENDADO PARA:"
        echo "    Horário UTC:   $PROXIMA_DATA_UTC"
        echo "    Horário Local: $PROXIMA_DATA_LOCAL"
        echo "=========================================="
        echo ""
    } | tee /dev/console /dev/tty1 2>/dev/null || true
    logger -t agendar-boot "✓ Próximo boot: $PROXIMA_DATA_UTC (Local: $PROXIMA_DATA_LOCAL)"
    sleep 2
    exit 0
else
    echo "✗ ERRO: rtcwake falhou ao gravar o agendamento (código $RC)!"
    logger -t agendar-boot "✗ ERRO: rtcwake falhou (código $RC)"
    exit 1
fi
