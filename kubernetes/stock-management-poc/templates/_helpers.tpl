{{- define "fullName" -}}
{{ .Release.Name }}
{{- end -}}

{{- define "labels" -}}
app: {{ .Release.Name }}
app.kubernetes.io/name: {{ .Release.Name }}
{{- end }}

{{- define "redisHeadlessLabels" -}}
app: {{ .Release.Name }}
app.kubernetes.io/name: {{ .Release.Name }}-redis-headless
{{- end }}

{{- define "redisMasterLabels" -}}
app: {{ .Release.Name }}
app.kubernetes.io/name: {{ .Release.Name }}-redis-master
{{- end }}

{{- define "redisLabels" -}}
app: {{ .Release.Name }}
app.kubernetes.io/name: {{ .Release.Name }}-redis
{{- end }}

{{- define "image" -}}
{{ .Values.service.image.repository }}/{{ .Values.service.image.name }}:{{ .Values.service.image.tag | default .Chart.AppVersion }}
{{- end -}}

