{{/*
Common labels
*/}}
{{- define "blacksentinel-pulse.labels" -}}
app.kubernetes.io/name: blacksentinel-pulse
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "blacksentinel-pulse.selectorLabels" -}}
app.kubernetes.io/name: blacksentinel-pulse
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
