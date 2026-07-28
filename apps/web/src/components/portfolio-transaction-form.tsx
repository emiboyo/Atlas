"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import { atlasApi } from "@/lib/api-client";
import { PortfolioNotice } from "@/components/portfolio-notice";

const transactionTypes = [
  ["virtual_deposit", "Record virtual deposit"],
  ["virtual_withdrawal", "Record virtual withdrawal"],
  ["simulated_buy", "Record simulated buy"],
  ["simulated_sell", "Record simulated sell"],
  ["simulated_dividend", "Record simulated dividend"],
  ["simulated_fee", "Record simulated fee"],
  ["simulated_split_adjustment", "Record simulated split adjustment"],
] as const;

export function PortfolioTransactionForm({ portfolioId }: { portfolioId: string }) {
  const { getToken } = useAuth();
  const [type, setType] = useState<(typeof transactionTypes)[number][0]>("virtual_deposit");
  const [currency, setCurrency] = useState("GBP");
  const [listingId, setListingId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unitPrice, setUnitPrice] = useState("");
  const [amount, setAmount] = useState("");
  const [fee, setFee] = useState("0");
  const [splitRatio, setSplitRatio] = useState("");
  const [effectiveAt, setEffectiveAt] = useState(new Date().toISOString().slice(0, 16));
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const tradeLike = type === "simulated_buy" || type === "simulated_sell";
  const listingRequired =
    tradeLike || type === "simulated_dividend" || type === "simulated_split_adjustment";
  const amountRequired = [
    "virtual_deposit",
    "virtual_withdrawal",
    "simulated_dividend",
    "simulated_fee",
  ].includes(type);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      const idempotencyKey = crypto.randomUUID();
      await atlasApi(`/portfolios/${portfolioId}/transactions`, token, {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
        body: JSON.stringify({
          transaction_type: type,
          currency,
          listing_id: listingId || null,
          quantity: quantity || null,
          unit_price: unitPrice || null,
          amount: amount || null,
          fee_amount: fee || "0",
          split_ratio: splitRatio || null,
          effective_at: new Date(effectiveAt).toISOString(),
          reason: reason || null,
          metadata: {},
        }),
      });
      window.location.assign(`/app/portfolios/${portfolioId}/transactions`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Simulated transaction failed.");
      document.querySelector<HTMLElement>('[role="alert"]')?.focus();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-7">
      <PortfolioNotice />
      <form
        onSubmit={(event) => void submit(event)}
        className="max-w-3xl rounded-2xl border border-white/10 bg-white/[0.03] p-6"
      >
        <h1 className="font-display text-3xl font-semibold">Record simulated activity</h1>
        <p className="mt-2 text-sm text-slate-400">
          This records internal paper-accounting entries only. It cannot contact a broker, bank,
          exchange, payment service, or external execution venue.
        </p>
        <p role="alert" tabIndex={-1} className="mt-4 text-sm text-rose-300">
          {message}
        </p>
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <label className="md:col-span-2">
            <span className="text-sm text-slate-300">Simulated transaction type</span>
            <select
              className="atlas-input mt-2"
              value={type}
              onChange={(event) =>
                setType(event.target.value as (typeof transactionTypes)[number][0])
              }
            >
              {transactionTypes.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="text-sm text-slate-300">Currency</span>
            <input
              className="atlas-input mt-2 uppercase"
              value={currency}
              pattern="[A-Z]{3}"
              maxLength={3}
              onChange={(event) => setCurrency(event.target.value.toUpperCase())}
              required
            />
          </label>
          <label>
            <span className="text-sm text-slate-300">Effective date and time</span>
            <input
              type="datetime-local"
              className="atlas-input mt-2"
              value={effectiveAt}
              onChange={(event) => setEffectiveAt(event.target.value)}
              required
            />
          </label>
          {listingRequired ? (
            <label className="md:col-span-2">
              <span className="text-sm text-slate-300">Atlas listing ID</span>
              <input
                className="atlas-input mt-2"
                value={listingId}
                onChange={(event) => setListingId(event.target.value)}
                required
              />
            </label>
          ) : null}
          {tradeLike ? (
            <>
              <DecimalInput label="Simulated quantity" value={quantity} setValue={setQuantity} />
              <DecimalInput
                label="Simulated unit price"
                value={unitPrice}
                setValue={setUnitPrice}
              />
              <DecimalInput label="Simulated fee" value={fee} setValue={setFee} allowZero />
            </>
          ) : null}
          {amountRequired ? (
            <DecimalInput label="Simulated amount" value={amount} setValue={setAmount} />
          ) : null}
          {type === "simulated_split_adjustment" ? (
            <DecimalInput
              label="Positive split ratio"
              value={splitRatio}
              setValue={setSplitRatio}
            />
          ) : null}
          <label className="md:col-span-2">
            <span className="text-sm text-slate-300">Bounded reason (optional)</span>
            <textarea
              className="atlas-input mt-2 min-h-24"
              value={reason}
              maxLength={500}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
        </div>
        <button
          disabled={submitting}
          className="mt-6 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
        >
          {submitting ? "Recording…" : transactionTypes.find(([value]) => value === type)?.[1]}
        </button>
      </form>
    </div>
  );
}

function DecimalInput({
  label,
  value,
  setValue,
  allowZero = false,
}: {
  label: string;
  value: string;
  setValue: (value: string) => void;
  allowZero?: boolean;
}) {
  return (
    <label>
      <span className="text-sm text-slate-300">{label}</span>
      <input
        inputMode="decimal"
        className="atlas-input mt-2"
        value={value}
        pattern={
          allowZero ? String.raw`\d+(\.\d{1,18})?` : String.raw`(?!0+(\.0+)?$)\d+(\.\d{1,18})?`
        }
        onChange={(event) => setValue(event.target.value)}
        required
      />
    </label>
  );
}
