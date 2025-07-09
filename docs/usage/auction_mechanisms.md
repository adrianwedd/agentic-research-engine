# Dynamic Auction Mechanism Configuration

The Market Maker service selects an auction format based on the workload
characteristics. Configuration thresholds control how that decision is made.

## Default Heuristics

```yaml
auction:
  high_complexity: 0.7  # threshold for SSI/VCG
  high_budget: 0.7      # budget required to trigger VCG
  many_tasks: 10        # task count to consider PSI/GCAA
```

These values map to the following strategies:

- **VCG** – chosen when both workload complexity and available budget exceed
  `high_complexity` and `high_budget`.
- **PSI** – used for large batches of simple tasks where `num_tasks >= many_tasks`
  and complexity is low (`<= 0.4`).
- **GCAA** – preferred for moderately complex workloads with several tasks.
- **SSI** – selected for complex tasks when the budget is limited.
- **Combinatorial** – the default when no other rule matches.

Adjust the thresholds in your configuration file or environment variables to
adapt selection behavior to your deployment.
