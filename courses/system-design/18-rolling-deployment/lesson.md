# Encoding and Evolution: A Rolling Deployment

Version 2 of your app adds two features: users can save a **phone number** and enter a **referral code**. The mobile team shipped the v2 app this morning, so right now **half your users run v1 and half run v2**. You're about to deploy the v2 API.

You can't stop the world to upgrade. The deploy is **rolling**: the load balancer drains one API server at a time, it restarts on v2, and rejoins. For a while, every combination happens:

| Client | Server | Needs |
|---|---|---|
| v1 app | v1 server | — |
| v2 app | v1 server | **forward** compatibility: old code reads new messages |
| v1 app | v2 server | **backward** compatibility: new code reads old messages |
| v2 app | v2 server | — |

Responses flow the other way, so each pairing needs both directions.

## The setup

- **2,000 requests over 2 seconds**, half from each app version.
- The rollout starts at 300 ms and upgrades one server every 500 ms. Each is out of rotation for 300 ms while it restarts. Watch the version badges change on the replay.
- The **Schema Registry** holds the message schemas, Protocol Buffers style. Readers match fields by **tag**.

v1 is already deployed and can't change:

| Tag | Field | Type | |
|---|---|---|---|
| 1 | `user_id` | int64 | required |
| 2 | `email` | string | required |
| 3 | `nickname` | string | optional |

## Your task

The v2 schema in the registry was written in a hurry. Click **Simulate Traffic** to see what the rollout does to it, then **double-click the Schema Registry** to fix v2 so that **no request fails** in either direction. v2 must still have the `phone` and `referral_code` fields: that's the feature you're shipping.

How readers decode, as in the last lesson:

- Tags a reader doesn't know are **skipped**.
- An **optional** field that's missing gets a default.
- A **required** field that's missing is an error.
- A tag whose **type** or **name** differs between versions breaks decoding, or worse, silently reads one field as another.

Keep the three API servers, too. With only one, the rolling deploy has nothing to send traffic to while it restarts.

> **Think about it.** Your fix lets v1 and v2 coexist. What would you have to do before you could ever make `phone` required? (Every client and every stored record would need it first, which in practice means never. That's why Protocol Buffers 3 dropped `required` entirely.)
