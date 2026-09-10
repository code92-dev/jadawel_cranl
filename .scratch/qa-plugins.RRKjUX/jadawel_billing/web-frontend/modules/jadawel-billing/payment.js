/** Card details are sent only to Moyasar; never use the Jadawel API client here. */
export async function submitPayment(
  order,
  key,
  card,
  callback,
  transport = fetch,
) {
  const response = await transport("https://api.moyasar.com/v1/payments", {
    method: "POST",
    credentials: "omit",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Basic " + btoa(key + ":"),
    },
    body: JSON.stringify({
      given_id: order.given_id || order.payment_id,
      amount: order.amount,
      currency: order.currency,
      callback_url: callback,
      description: "Jadawel subscription",
      metadata: { billing_order: order.id },
      source: {
        type: "creditcard",
        ...card,
        month: Number(card.month),
        year: Number(card.year),
      },
    }),
  });
  if (!response.ok) throw new Error("payment_pending_verification");
  return await response.json();
}
