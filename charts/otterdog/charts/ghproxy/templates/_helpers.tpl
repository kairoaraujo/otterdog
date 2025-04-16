#
#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************
#
{{/*
Expand the name of the chart.
*/}}
{{- define "ghproxy.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ghproxy.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ghproxy.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ghproxy.labels" -}}
helm.sh/chart: {{ include "ghproxy.chart" . }}
{{ include "ghproxy.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ghproxy.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ghproxy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ghproxy.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ghproxy.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Extract Redis host from URI
*/}}
{{- define "ghproxy.redis.host" -}}
{{- $uri := .Values.redisAddress | default "" -}}
{{- /* Try extracting host after @ if auth is present */ -}}
{{- $host := regexFind "@([^:/]+)" $uri | trimPrefix "@" -}}
{{- /* If no auth, get the host directly after scheme or start of string */ -}}
{{- if not $host }}
{{- $host = regexFind "^([^:@/]+)" (regexReplaceAll "^redis://(.*)" $uri "${1}") -}}
{{- end }}
{{- $host -}}
{{- end -}}


{{/*
Extract Redis port from URI
*/}}
{{- define "ghproxy.redis.port" -}}
{{- $uri := .Values.redisAddress | default "" -}}
{{- $port := regexFind ":([0-9]+)$" $uri | trimPrefix ":" -}}
{{- default "6379" $port -}}
{{- end -}}