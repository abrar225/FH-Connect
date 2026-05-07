"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Bell, Bot, CheckCircle2, Link2, Loader2, Save, Settings, Shield, User } from "lucide-react";
import { authFetch } from "@/app/lib/api";

type SettingsRow = {
  profile?: Record<string, unknown>;
  notification_preferences?: Record<string, unknown>;
  default_report_format?: string;
  ai_preferences?: Record<string, unknown>;
  security_preferences?: Record<string, unknown>;
  data_retention_days?: number;
};

type IntegrationRow = {
  provider: string;
  status: string;
  config?: Record<string, unknown>;
  secret_ref?: string | null;
};

const providers = ["slack", "linear", "jira", "google_calendar", "gmail", "google_drive"];
const aiProviders = [
  {
    id: "gemini",
    label: "Google Gemini",
    models: ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-latest"],
  },
  {
    id: "gemma",
    label: "Google Gemma",
    models: ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemma-3-27b-it", "gemma-3-12b-it", "gemma-3-4b-it", "gemma-3n-e4b-it", "gemma-3n-e2b-it", "gemma-3-1b-it"],
  },
  {
    id: "groq",
    label: "Groq",
    models: ["llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct"],
  },
  {
    id: "custom",
    label: "Custom Provider",
    models: ["custom"],
  },
];

const defaultSettings: SettingsRow = {
  profile: {},
  notification_preferences: { email_summary: true, action_reminders: true },
  default_report_format: "markdown",
  ai_preferences: { provider: "gemini", model: "gemini-2.5-flash" },
  security_preferences: { share_expiry_required: true },
  data_retention_days: 365,
};

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as Record<string, unknown> : {};
    } catch {
      return {};
    }
  }
  return {};
}

function normalizeSettings(row: SettingsRow): SettingsRow {
  return {
    ...defaultSettings,
    ...row,
    profile: asRecord(row.profile),
    notification_preferences: {
      ...asRecord(defaultSettings.notification_preferences),
      ...asRecord(row.notification_preferences),
    },
    ai_preferences: {
      ...asRecord(defaultSettings.ai_preferences),
      ...asRecord(row.ai_preferences),
    },
    security_preferences: {
      ...asRecord(defaultSettings.security_preferences),
      ...asRecord(row.security_preferences),
    },
    data_retention_days: Number(row.data_retention_days || defaultSettings.data_retention_days),
  };
}

async function readApiError(res: Response, fallback: string) {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item?.msg || JSON.stringify(item)).join(" ");
    }
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (typeof body?.message === "string" && body.message.trim()) {
      return body.message;
    }
  } catch {
    // Response body is optional; use the fallback below.
  }
  return `${fallback} (${res.status})`;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsRow | null>(null);
  const [integrations, setIntegrations] = useState<IntegrationRow[]>([]);
  const [provider, setProvider] = useState("slack");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [apiKeyDraft, setApiKeyDraft] = useState("");

  const load = useCallback(async () => {
    try {
      const [settingsRes, integrationsRes] = await Promise.all([
        authFetch("/api/settings"),
        authFetch("/api/integrations"),
      ]);
      if (settingsRes.ok) {
        setSettings(normalizeSettings(await settingsRes.json()));
      } else {
        setSettings(normalizeSettings(defaultSettings));
        setMessage("Backend settings are unavailable. You can still edit defaults locally, then retry saving.");
      }
      if (integrationsRes.ok) setIntegrations(await integrationsRes.json());
    } catch {
      setSettings(normalizeSettings(defaultSettings));
      setMessage("Backend settings are unavailable. You can still edit defaults locally, then retry saving.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const updateField = (key: keyof SettingsRow, value: unknown) => {
    setSettings((current) => ({ ...(current || {}), [key]: value }));
  };

  const saveSettings = async () => {
    if (!settings) return;
    setSaving(true);
    setMessage("");
    try {
      const res = await authFetch("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          profile: asRecord(settings.profile),
          notification_preferences: asRecord(settings.notification_preferences),
          default_report_format: settings.default_report_format || "markdown",
          ai_preferences: {
            ...asRecord(settings.ai_preferences),
            ...(apiKeyDraft.trim() ? { api_key: apiKeyDraft.trim() } : {}),
          },
          security_preferences: asRecord(settings.security_preferences),
          data_retention_days: settings.data_retention_days || 365,
        }),
      });
      if (res.ok) {
        setSettings(normalizeSettings(await res.json()));
        setApiKeyDraft("");
        setMessage("Settings saved.");
      } else {
        setMessage(await readApiError(res, "Settings could not be saved."));
      }
    } catch {
      setMessage("Backend unavailable. Please confirm the backend server is running and try again.");
    } finally {
      setSaving(false);
    }
  };

  const saveIntegration = async () => {
    setMessage("");
    const res = await authFetch("/api/integrations", {
      method: "POST",
      body: JSON.stringify({
        provider,
        status: webhookUrl ? "active" : "configured",
        config: webhookUrl ? { webhook_url: webhookUrl } : {},
      }),
    });
    setMessage(res.ok ? "Integration saved." : "Integration could not be saved.");
    if (res.ok) load();
  };

  if (!settings) {
    return <div className="p-8 text-gray-400">Loading settings...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto h-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white">Settings</h1>
        <p className="text-gray-400 mt-2">Profile, workspace defaults, AI behavior, notifications, integrations, sessions, and retention controls.</p>
      </div>

      {message && <div className="mb-5 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-300">{message}</div>}

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel icon={User} title="Profile">
          <TextInput label="Display name" value={String(settings.profile?.name || "")} onChange={(value) => updateField("profile", { ...(settings.profile || {}), name: value })} />
          <TextInput label="Email" value={String(settings.profile?.email || "")} onChange={(value) => updateField("profile", { ...(settings.profile || {}), email: value })} />
        </Panel>

        <Panel icon={Settings} title="Report Defaults">
          <label className="block">
            <span className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Default report format</span>
            <select value={settings.default_report_format || "markdown"} onChange={(event) => updateField("default_report_format", event.target.value)} className="w-full rounded-xl border border-white/10 bg-surface/80 px-3 py-2.5 text-sm text-white outline-none">
              <option value="markdown">Markdown</option>
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
            </select>
          </label>
          <TextInput label="Data retention days" type="number" value={String(settings.data_retention_days || 365)} onChange={(value) => updateField("data_retention_days", Number(value))} />
        </Panel>

        <Panel icon={Bot} title="AI Provider">
          <AIProviderSettings
            preferences={settings.ai_preferences || {}}
            apiKeyDraft={apiKeyDraft}
            onApiKeyDraftChange={setApiKeyDraft}
            onChange={(next) => updateField("ai_preferences", next)}
          />
        </Panel>

        <Panel icon={Bell} title="Notifications">
          <Toggle label="Email summaries" checked={Boolean(settings.notification_preferences?.email_summary ?? true)} onChange={(checked) => updateField("notification_preferences", { ...(settings.notification_preferences || {}), email_summary: checked })} />
          <Toggle label="Action reminders" checked={Boolean(settings.notification_preferences?.action_reminders ?? true)} onChange={(checked) => updateField("notification_preferences", { ...(settings.notification_preferences || {}), action_reminders: checked })} />
        </Panel>

        <Panel icon={Shield} title="Security">
          <Toggle label="Share links require expiry" checked={Boolean(settings.security_preferences?.share_expiry_required ?? true)} onChange={(checked) => updateField("security_preferences", { ...(settings.security_preferences || {}), share_expiry_required: checked })} />
          <p className="text-sm text-gray-500">Authentication is handled by Supabase Google sign-in. Backend APIs verify tokens and meeting permissions before returning data.</p>
        </Panel>

        <Panel icon={Link2} title="Integrations">
          <div className="grid gap-3 md:grid-cols-[160px_1fr]">
            <select value={provider} onChange={(event) => setProvider(event.target.value)} className="rounded-xl border border-white/10 bg-surface/80 px-3 py-2.5 text-sm text-white outline-none">
              {providers.map((item) => <option key={item} value={item}>{item.replace("_", " ")}</option>)}
            </select>
            <input value={webhookUrl} onChange={(event) => setWebhookUrl(event.target.value)} placeholder="Webhook URL or adapter endpoint" className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none placeholder:text-gray-500" />
          </div>
          <button onClick={saveIntegration} className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-semibold text-gray-200"><CheckCircle2 className="h-4 w-4" /> Save Integration</button>
          <div className="space-y-2 pt-1">
            {integrations.map((item) => (
              <div key={item.provider} className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <span className="text-gray-200">{item.provider.replace("_", " ")}</span>
                <span className="text-xs uppercase tracking-wide text-gray-500">{item.status}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <button onClick={saveSettings} disabled={saving} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        Save Settings
      </button>
    </div>
  );
}

function AIProviderSettings({
  preferences,
  apiKeyDraft,
  onApiKeyDraftChange,
  onChange,
}: {
  preferences: Record<string, unknown>;
  apiKeyDraft: string;
  onApiKeyDraftChange: (value: string) => void;
  onChange: (value: Record<string, unknown>) => void;
}) {
  const provider = String(preferences.provider || "gemini");
  const selectedProvider = aiProviders.find((item) => item.id === provider) || aiProviders[0];
  const model = String(preferences.model || selectedProvider.models[0]);
  const apiKeyStatus = preferences.api_key_status as Record<string, { configured?: boolean; last4?: string }> | undefined;
  const providerKeyStatus = apiKeyStatus?.[provider];

  const updateProvider = (nextProvider: string) => {
    const nextProviderConfig = aiProviders.find((item) => item.id === nextProvider) || aiProviders[0];
    onChange({
      ...preferences,
      provider: nextProvider,
      model: nextProviderConfig.models[0],
    });
    onApiKeyDraftChange("");
  };

  const updateModel = (nextModel: string) => {
    onChange({ ...preferences, model: nextModel });
  };

  return (
    <div className="space-y-4">
      <label className="block">
        <span className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Provider</span>
        <select value={provider} onChange={(event) => updateProvider(event.target.value)} className="w-full rounded-xl border border-white/10 bg-surface/80 px-3 py-2.5 text-sm text-white outline-none">
          {aiProviders.map((item) => (
            <option key={item.id} value={item.id}>{item.label}</option>
          ))}
        </select>
      </label>

      {provider === "custom" ? (
        <>
          <TextInput label="Custom provider id" value={String(preferences.custom_provider || "")} onChange={(value) => onChange({ ...preferences, custom_provider: value, provider: "custom" })} />
          <TextInput label="Custom model name" value={String(preferences.model === "custom" ? "" : preferences.model || "")} onChange={(value) => onChange({ ...preferences, model: value })} />
        </>
      ) : (
        <label className="block">
          <span className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Model</span>
          <select value={model} onChange={(event) => updateModel(event.target.value)} className="w-full rounded-xl border border-white/10 bg-surface/80 px-3 py-2.5 text-sm text-white outline-none">
            {selectedProvider.models.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      )}

      <TextInput
        label="Preferred custom model override"
        value={String(preferences.custom_model || "")}
        onChange={(value) => onChange({ ...preferences, custom_model: value })}
      />

      <label className="block">
        <span className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Provider API key</span>
        <input
          type="password"
          value={apiKeyDraft}
          onChange={(event) => onApiKeyDraftChange(event.target.value)}
          placeholder={providerKeyStatus?.configured ? `Saved key ending in ${providerKeyStatus.last4}` : "Paste API key to save or rotate"}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none placeholder:text-gray-500"
        />
        <p className="mt-2 text-xs leading-relaxed text-gray-500">
          Saved keys are encrypted server-side and are not returned to the browser. Leave this blank to keep the existing key.
        </p>
      </label>
    </div>
  );
}

function Panel({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-white/10 bg-surface/40 p-5">
      <div className="mb-4 flex items-center gap-3">
        <Icon className="h-5 w-5 text-primary" />
        <h2 className="font-semibold text-white">{title}</h2>
      </div>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function TextInput({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none placeholder:text-gray-500" />
    </label>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
      <span className="text-sm text-gray-200">{label}</span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="h-4 w-4 accent-primary" />
    </label>
  );
}
