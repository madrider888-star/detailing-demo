"use client";

import { useId, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { bookingTarget, site } from "@/content/site";
import { ui } from "@/content/ui";
import { services } from "@/content/services";
import { t, type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

type FieldName = "name" | "phone" | "email" | "make" | "model" | "year" | "service" | "date" | "message";
type Values = Record<FieldName, string>;
type Errors = Partial<Record<FieldName, string>>;

const emptyValues: Values = {
  name: "",
  phone: "",
  email: "",
  make: "",
  model: "",
  year: "",
  service: "",
  date: "",
  message: "",
};

const inputClasses =
  "h-12 w-full rounded-button border border-line bg-ink-900 px-4 text-[15px] text-chalk-50 " +
  "placeholder:text-chalk-500 transition-colors duration-300 hover:border-line-strong " +
  "focus:border-accent focus:outline-none aria-[invalid=true]:border-red-400/70";

function Field({
  label,
  htmlFor,
  error,
  hint,
  required,
  children,
  className,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <label
        htmlFor={htmlFor}
        className="text-[11px] font-medium tracking-[0.16em] text-chalk-400 uppercase"
      >
        {label}
        {required ? <span className="ml-1 text-accent">*</span> : null}
      </label>
      {children}
      {error ? (
        <p id={`${htmlFor}-error`} role="alert" className="text-[12.5px] text-red-400">
          {error}
        </p>
      ) : hint ? (
        <p className="text-[12.5px] text-chalk-500">{hint}</p>
      ) : null}
    </div>
  );
}

/**
 * Booking request form.
 *
 * On submit the request is posted to /api/lead, which forwards it to the
 * studio's Telegram. If that endpoint is not configured yet (no bot token in
 * the hosting environment) the form falls back to the original hand-off:
 * it composes the enquiry as text and opens the studio's messenger or e-mail
 * with it prefilled, plus a copy-to-clipboard button.
 */
export function BookingForm({
  locale,
  defaultService = "",
  defaultMessage = "",
}: {
  locale: Locale;
  defaultService?: string;
  /** Prefilled message, e.g. from a "discuss a similar project" button. */
  defaultMessage?: string;
}) {
  const formId = useId();
  const [values, setValues] = useState<Values>({
    ...emptyValues,
    service: defaultService,
    message: defaultMessage,
  });
  const [errors, setErrors] = useState<Errors>({});
  const [sent, setSent] = useState<string | null>(null);
  const [delivered, setDelivered] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState(false);
  const [copied, setCopied] = useState(false);
  const [company, setCompany] = useState("");
  const pathname = usePathname();

  const fieldId = (name: FieldName) => `${formId}-${name}`;
  const label = (key: keyof typeof ui.form) => t(ui.form[key] as { uk: string; en: string }, locale);

  const setValue = (name: FieldName, value: string) => {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => {
      if (!current[name]) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
  };

  function validate(): Errors {
    const found: Errors = {};
    if (values.name.trim().length < 2) found.name = t(ui.form.errors.name, locale);
    if (!/^[+\d][\d\s()-]{7,}$/.test(values.phone.trim()))
      found.phone = t(ui.form.errors.phone, locale);
    if (values.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(values.email.trim()))
      found.email = t(ui.form.errors.email, locale);
    if (values.make.trim().length < 2) found.make = t(ui.form.errors.make, locale);
    if (values.model.trim().length < 1) found.model = t(ui.form.errors.model, locale);
    if (services.length > 0 && !values.service) found.service = t(ui.form.errors.service, locale);
    return found;
  }

  /** Renders the enquiry as plain text for whichever channel receives it. */
  function compose(): string {
    const chosen = services.find((service) => service.slug === values.service);
    const lines = [
      `${label("heading")} — ${site.name}`,
      `${label("name")}: ${values.name}`,
      `${label("phone")}: ${values.phone}`,
      values.email ? `${label("email")}: ${values.email}` : null,
      `${label("vehicle")}: ${values.make} ${values.model}${values.year ? ` (${values.year})` : ""}`,
      chosen ? `${label("service")}: ${t(chosen.title, locale)}` : null,
      values.date ? `${label("date")}: ${values.date}` : null,
      values.message ? `${label("message")}: ${values.message}` : null,
    ];
    return lines.filter((line) => line !== null).join("\n");
  }

  /** Opens the studio's channel with the enquiry prefilled. */
  function handoff(text: string) {
    const channel = bookingTarget();
    // Telegram and WhatsApp accept the message as a query parameter, so the
    // chat opens with the request already typed — the client only presses Send.
    if (channel?.href.startsWith("https://wa.me/") || channel?.href.startsWith("https://t.me/")) {
      const url = new URL(channel.href);
      url.searchParams.set("text", text);
      window.open(url.toString(), "_blank", "noopener");
      return;
    }
    if (site.email) {
      const subject = encodeURIComponent(`${label("heading")} — ${values.make} ${values.model}`);
      window.location.href = `mailto:${site.email}?subject=${subject}&body=${encodeURIComponent(text)}`;
      return;
    }
    if (channel) window.open(channel.href, "_blank", "noopener");
  }

  /** Sends the request to the site's own endpoint. Resolves to true when it was delivered. */
  async function deliver(): Promise<boolean> {
    const chosen = services.find((service) => service.slug === values.service);
    try {
      const response = await fetch("/api/lead", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ...values,
          service: chosen ? t(chosen.title, locale) : values.service,
          company,
          locale,
          page: pathname,
        }),
      });
      const result = (await response.json()) as { ok: boolean; reason?: string };
      if (result.ok) return true;
      if (result.reason === "not-configured") return false;
      throw new Error(result.reason);
    } catch {
      setServerError(true);
      return false;
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate();
    setErrors(found);

    if (Object.keys(found).length > 0) {
      const first = Object.keys(found)[0] as FieldName | undefined;
      if (first) document.getElementById(fieldId(first))?.focus();
      return;
    }

    const text = compose();

    // Messenger hand-off must run synchronously inside the click, or the
    // browser treats the new window as a pop-up and blocks it.
    if (site.leads !== "bot") {
      setSent(text);
      handoff(text);
      return;
    }

    setSubmitting(true);
    setServerError(false);
    const ok = await deliver();
    setSubmitting(false);

    if (ok) {
      setDelivered(true);
      setSent(text);
      return;
    }
    // Not configured (or unreachable): the messenger hand-off still works.
    setSent(text);
    handoff(text);
  }

  if (sent !== null && delivered) {
    return (
      <div className="rounded-card border border-accent/30 bg-ink-850 p-8 sm:p-10" role="status">
        <span className="grid h-12 w-12 place-items-center rounded-button bg-accent/12 text-accent">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-5 w-5">
            <path
              d="M4 10.5 8 14.5 16 5.5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <h3 className="mt-6 font-display text-2xl font-semibold uppercase">
          {t(ui.form.successSentTitle, locale)}
        </h3>
        <p className="mt-3 max-w-md text-[15px] leading-relaxed text-chalk-400">
          {t(ui.form.successSentBody, locale)}
        </p>
        <div className="mt-8">
          <Button
            variant="ghost"
            onClick={() => {
              setValues({ ...emptyValues, service: defaultService, message: defaultMessage });
              setDelivered(false);
              setSent(null);
            }}
          >
            {t(ui.form.successAgain, locale)}
          </Button>
        </div>
      </div>
    );
  }

  if (sent !== null) {
    return (
      <div className="rounded-card border border-accent/30 bg-ink-850 p-8 sm:p-10" role="status">
        <span className="grid h-12 w-12 place-items-center rounded-button bg-accent/12 text-accent">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-5 w-5">
            <path
              d="M4 10.5 8 14.5 16 5.5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <h3 className="mt-6 font-display text-2xl font-semibold uppercase">
          {t(ui.form.successTitle, locale)}
        </h3>
        <p className="mt-3 max-w-md text-[15px] leading-relaxed text-chalk-400">
          {t(ui.form.successBody, locale)}
        </p>

        <pre className="mt-6 max-h-56 overflow-auto rounded-card border border-line bg-ink-900 p-4 text-[13px] leading-relaxed whitespace-pre-wrap text-chalk-300">
          {sent}
        </pre>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={() => {
              void navigator.clipboard?.writeText(sent).then(() => setCopied(true));
            }}
          >
            {copied ? "✓" : null}
            {locale === "uk" ? "Скопіювати текст" : "Copy the text"}
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setValues({ ...emptyValues, service: defaultService, message: defaultMessage });
              setCopied(false);
              setSent(null);
            }}
          >
            {t(ui.form.successAgain, locale)}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form noValidate onSubmit={onSubmit} className="relative grid gap-6 sm:grid-cols-2">
      <Field label={label("name")} htmlFor={fieldId("name")} error={errors.name} required>
        <input
          id={fieldId("name")}
          name="name"
          type="text"
          autoComplete="name"
          placeholder={label("namePlaceholder")}
          value={values.name}
          onChange={(event) => setValue("name", event.target.value)}
          aria-invalid={Boolean(errors.name)}
          className={inputClasses}
        />
      </Field>

      <Field label={label("phone")} htmlFor={fieldId("phone")} error={errors.phone} required>
        <input
          id={fieldId("phone")}
          name="phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="+380"
          value={values.phone}
          onChange={(event) => setValue("phone", event.target.value)}
          aria-invalid={Boolean(errors.phone)}
          className={inputClasses}
        />
      </Field>

      <Field
        label={label("emailOptional")}
        htmlFor={fieldId("email")}
        error={errors.email}
        className="sm:col-span-2"
      >
        <input
          id={fieldId("email")}
          name="email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={values.email}
          onChange={(event) => setValue("email", event.target.value)}
          aria-invalid={Boolean(errors.email)}
          className={inputClasses}
        />
      </Field>

      <fieldset className="grid gap-6 sm:col-span-2 sm:grid-cols-3">
        <legend className="mb-4 text-[11px] font-medium tracking-[0.16em] text-chalk-500 uppercase">
          {label("vehicle")}
        </legend>
        <Field label={label("make")} htmlFor={fieldId("make")} error={errors.make} required>
          <input
            id={fieldId("make")}
            name="make"
            type="text"
            value={values.make}
            onChange={(event) => setValue("make", event.target.value)}
            aria-invalid={Boolean(errors.make)}
            className={inputClasses}
          />
        </Field>
        <Field label={label("model")} htmlFor={fieldId("model")} error={errors.model} required>
          <input
            id={fieldId("model")}
            name="model"
            type="text"
            value={values.model}
            onChange={(event) => setValue("model", event.target.value)}
            aria-invalid={Boolean(errors.model)}
            className={inputClasses}
          />
        </Field>
        <Field label={label("carYear")} htmlFor={fieldId("year")}>
          <input
            id={fieldId("year")}
            name="year"
            type="number"
            inputMode="numeric"
            min={1950}
            max={new Date().getFullYear() + 1}
            value={values.year}
            onChange={(event) => setValue("year", event.target.value)}
            className={inputClasses}
          />
        </Field>
      </fieldset>

      {services.length > 0 ? (
        <Field label={label("service")} htmlFor={fieldId("service")} error={errors.service} required>
          <select
            id={fieldId("service")}
            name="service"
            value={values.service}
            onChange={(event) => setValue("service", event.target.value)}
            aria-invalid={Boolean(errors.service)}
            className={cn(inputClasses, "appearance-none pr-10")}
          >
            <option value="">{label("servicePlaceholder")}</option>
            {services.map((service) => (
              <option key={service.slug} value={service.slug}>
                {t(service.title, locale)}
              </option>
            ))}
            <option value="unsure">{label("serviceUnsure")}</option>
          </select>
        </Field>
      ) : null}

      <Field label={label("date")} htmlFor={fieldId("date")} hint={label("dateHint")}>
        <input
          id={fieldId("date")}
          name="date"
          type="date"
          min={new Date().toISOString().slice(0, 10)}
          value={values.date}
          onChange={(event) => setValue("date", event.target.value)}
          className={cn(inputClasses, "[color-scheme:dark]")}
        />
      </Field>

      <Field
        label={label("message")}
        htmlFor={fieldId("message")}
        hint={label("messageHint")}
        className="sm:col-span-2"
      >
        <textarea
          id={fieldId("message")}
          name="message"
          rows={5}
          placeholder={label("messagePlaceholder")}
          value={values.message}
          onChange={(event) => setValue("message", event.target.value)}
          className={cn(inputClasses, "h-auto resize-y py-3 leading-relaxed")}
        />
      </Field>

      {/* Honeypot: hidden from people, filled in by bots. */}
      <div aria-hidden="true" className="absolute -left-[9999px] top-auto h-px w-px overflow-hidden">
        <label htmlFor={fieldId("company" as FieldName)}>Company</label>
        <input
          id={fieldId("company" as FieldName)}
          name="company"
          type="text"
          tabIndex={-1}
          autoComplete="off"
          value={company}
          onChange={(event) => setCompany(event.target.value)}
        />
      </div>

      {serverError ? (
        <p role="alert" className="text-[13px] text-red-400 sm:col-span-2">
          {t(ui.form.errors.server, locale)}
        </p>
      ) : null}

      <div className="flex flex-col gap-5 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
        {site.messaging.length > 0 ? (
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-[13px] text-chalk-500">{t(ui.form.sendVia, locale)}</span>
            {site.messaging.map((channel) => (
              <a
                key={channel.href}
                href={channel.href}
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-2 text-[14px] text-chalk-200 transition-colors hover:text-accent"
              >
                <Icon name={channel.icon} className="h-4 w-4" />
                {channel.label}
              </a>
            ))}
          </div>
        ) : (
          <span />
        )}
        <Button size="lg" type="submit" disabled={submitting} className="sm:min-w-56">
          {t(submitting ? ui.form.submitting : ui.form.submit, locale)}
        </Button>
      </div>
    </form>
  );
}
