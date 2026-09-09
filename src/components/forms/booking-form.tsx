"use client";

import { useId, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { services } from "@/content/services";
import { cn } from "@/lib/utils";

type FieldName =
  | "name"
  | "phone"
  | "email"
  | "make"
  | "model"
  | "year"
  | "service"
  | "date"
  | "message";

type Values = Record<FieldName, string>;
type Errors = Partial<Record<FieldName, string>>;

const initialValues: Values = {
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
  "h-12 w-full rounded-xl border border-white/10 bg-carbon-900 px-4 text-[15px] text-mist-100 " +
  "placeholder:text-mist-500 transition-colors duration-300 hover:border-white/18 " +
  "focus:border-brass-500/50 focus:outline-none aria-[invalid=true]:border-red-400/60";

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
        className="text-[12px] font-medium tracking-[0.14em] text-mist-400 uppercase"
      >
        {label}
        {required ? <span className="ml-1 text-brass-500">*</span> : null}
      </label>
      {children}
      {error ? (
        <p id={`${htmlFor}-error`} role="alert" className="text-[12.5px] text-red-400">
          {error}
        </p>
      ) : hint ? (
        <p id={`${htmlFor}-hint`} className="text-[12.5px] text-mist-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function validate(values: Values): Errors {
  const errors: Errors = {};
  const currentYear = new Date().getFullYear();

  if (values.name.trim().length < 2) errors.name = "Please tell us your name.";
  if (!/^[+\d][\d\s()-]{7,}$/.test(values.phone.trim()))
    errors.phone = "Enter a phone number we can reach you on.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(values.email.trim()))
    errors.email = "Enter a valid email address.";
  if (values.make.trim().length < 2) errors.make = "Required.";
  if (values.model.trim().length < 1) errors.model = "Required.";

  const year = Number(values.year);
  if (!values.year.trim() || Number.isNaN(year) || year < 1950 || year > currentYear + 1)
    errors.year = `Between 1950 and ${currentYear + 1}.`;

  if (!values.service) errors.service = "Choose a service so we can quote accurately.";

  return errors;
}

export function BookingForm({ defaultService = "" }: { defaultService?: string }) {
  const formId = useId();
  const [values, setValues] = useState<Values>({ ...initialValues, service: defaultService });
  const [errors, setErrors] = useState<Errors>({});
  const [status, setStatus] = useState<"idle" | "submitting" | "sent">("idle");

  const fieldId = (name: FieldName) => `${formId}-${name}`;

  const setValue = (name: FieldName, value: string) => {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => {
      if (!current[name]) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
  };

  const describedBy = (name: FieldName) => (errors[name] ? `${fieldId(name)}-error` : undefined);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);

    if (Object.keys(found).length > 0) {
      const firstKey = Object.keys(found)[0] as FieldName | undefined;
      if (firstKey) document.getElementById(fieldId(firstKey))?.focus();
      return;
    }

    // Demo build: no backend yet. The request is acknowledged locally so the
    // full booking journey can be reviewed end to end.
    setStatus("submitting");
    await new Promise((resolve) => setTimeout(resolve, 700));
    setStatus("sent");
  }

  if (status === "sent") {
    const chosen = services.find((service) => service.slug === values.service);
    return (
      <div className="rounded-2xl border border-brass-500/25 bg-carbon-850 p-8 sm:p-10" role="status">
        <span className="grid h-12 w-12 place-items-center rounded-full bg-brass-500/12 text-brass-400">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-5 w-5">
            <path
              d="M4 10.5 8 14.5 16 5.5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <h3 className="mt-6 font-display text-2xl font-semibold">Request received</h3>
        <p className="mt-3 max-w-md text-[15px] leading-relaxed text-mist-400">
          Thank you, {values.name.split(" ")[0]}. We will confirm availability for
          {chosen ? ` ${chosen.title.toLowerCase()}` : " your booking"} on your{" "}
          {values.year} {values.make} {values.model} within one working day.
        </p>
        <p className="mt-6 text-[13px] text-mist-500">
          This is a demo studio — no message was actually sent.
        </p>
        <Button
          variant="secondary"
          className="mt-8"
          onClick={() => {
            setValues({ ...initialValues, service: defaultService });
            setStatus("idle");
          }}
        >
          Send another request
        </Button>
      </div>
    );
  }

  return (
    <form noValidate onSubmit={onSubmit} className="grid gap-6 sm:grid-cols-2">
      <Field label="Full name" htmlFor={fieldId("name")} error={errors.name} required>
        <input
          id={fieldId("name")}
          name="name"
          type="text"
          autoComplete="name"
          placeholder="Andriy Kovalenko"
          value={values.name}
          onChange={(event) => setValue("name", event.target.value)}
          aria-invalid={Boolean(errors.name)}
          aria-describedby={describedBy("name")}
          className={inputClasses}
        />
      </Field>

      <Field label="Phone" htmlFor={fieldId("phone")} error={errors.phone} required>
        <input
          id={fieldId("phone")}
          name="phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="+380 67 000 00 00"
          value={values.phone}
          onChange={(event) => setValue("phone", event.target.value)}
          aria-invalid={Boolean(errors.phone)}
          aria-describedby={describedBy("phone")}
          className={inputClasses}
        />
      </Field>

      <Field
        label="Email"
        htmlFor={fieldId("email")}
        error={errors.email}
        required
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
          aria-describedby={describedBy("email")}
          className={inputClasses}
        />
      </Field>

      <fieldset className="grid gap-6 sm:col-span-2 sm:grid-cols-3">
        <legend className="mb-4 text-[12px] font-medium tracking-[0.14em] text-mist-500 uppercase">
          Vehicle
        </legend>
        <Field label="Make" htmlFor={fieldId("make")} error={errors.make} required>
          <input
            id={fieldId("make")}
            name="make"
            type="text"
            placeholder="Porsche"
            value={values.make}
            onChange={(event) => setValue("make", event.target.value)}
            aria-invalid={Boolean(errors.make)}
            aria-describedby={describedBy("make")}
            className={inputClasses}
          />
        </Field>
        <Field label="Model" htmlFor={fieldId("model")} error={errors.model} required>
          <input
            id={fieldId("model")}
            name="model"
            type="text"
            placeholder="911 Carrera S"
            value={values.model}
            onChange={(event) => setValue("model", event.target.value)}
            aria-invalid={Boolean(errors.model)}
            aria-describedby={describedBy("model")}
            className={inputClasses}
          />
        </Field>
        <Field label="Year" htmlFor={fieldId("year")} error={errors.year} required>
          <input
            id={fieldId("year")}
            name="year"
            type="number"
            inputMode="numeric"
            min={1950}
            max={new Date().getFullYear() + 1}
            placeholder="2021"
            value={values.year}
            onChange={(event) => setValue("year", event.target.value)}
            aria-invalid={Boolean(errors.year)}
            aria-describedby={describedBy("year")}
            className={inputClasses}
          />
        </Field>
      </fieldset>

      <Field label="Service" htmlFor={fieldId("service")} error={errors.service} required>
        <select
          id={fieldId("service")}
          name="service"
          value={values.service}
          onChange={(event) => setValue("service", event.target.value)}
          aria-invalid={Boolean(errors.service)}
          aria-describedby={describedBy("service")}
          className={cn(inputClasses, "appearance-none bg-carbon-900 pr-10")}
        >
          <option value="">Select a service</option>
          {services.map((service) => (
            <option key={service.slug} value={service.slug}>
              {service.title}
            </option>
          ))}
          <option value="not-sure">Not sure yet — advise me</option>
        </select>
      </Field>

      <Field
        label="Preferred date"
        htmlFor={fieldId("date")}
        hint="We confirm the exact slot by phone."
      >
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
        label="Message"
        htmlFor={fieldId("message")}
        hint="Paint condition, previous work, anything we should know."
        className="sm:col-span-2"
      >
        <textarea
          id={fieldId("message")}
          name="message"
          rows={5}
          placeholder="The car is two years old, mostly motorway miles, and the front bumper has picked up stone chips."
          value={values.message}
          onChange={(event) => setValue("message", event.target.value)}
          className={cn(inputClasses, "h-auto resize-y py-3 leading-relaxed")}
        />
      </Field>

      <div className="flex flex-col gap-4 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-sm text-[13px] leading-relaxed text-mist-500">
          Demo form — submissions are handled in the browser and never leave your device.
        </p>
        <Button size="lg" type="submit" disabled={status === "submitting"} className="sm:min-w-52">
          {status === "submitting" ? "Sending…" : "Request booking"}
        </Button>
      </div>
    </form>
  );
}
