---
title: "The Future of Mechanistic Interpretability in Alignment"
date: "2026-05-12"
slug: "mech-interp-for-alignment"
summary: "If a complete mechanistic explanation of a model is unrealistic, does mech interp still provide value for safety and alignment?"
key_points:
  - >-
    **Complete mechanistic understanding may not be necessary for interpretability to be useful.**
    Even if we can't fully explain how models work, partial understanding of their internal
    computations could still provide valuable evidence about alignment.
  - >-
    **Mechanistic interpretability may be more promising as a tool for measurement than intervention.**
    Identifying safety-relevant representations and understanding how they change during training
    seems more tractable than directly manipulating internal mechanisms to reliably control model behavior.
  - >-
    **Models' explanations of their own reasoning aren't necessarily faithful.**
    Chain-of-thought reasoning can provide useful insight into model behavior, but it can also
    omit important causal factors. Mechanistic interpretability offers a potential way to
    independently investigate whether models are actually reasoning as they claim.
  - >-
    **A particularly promising application is investigating whether models have internalized the principles we intended to teach them.**
    Rather than relying exclusively on behavioral evaluations, mechanistic methods could help
    distinguish models that genuinely apply learned safety principles from those relying on superficial heuristics.
  - >-
    **The goal shouldn't necessarily be to explain everything a model does, but to discover when it isn't doing what we think it is.**
    Mechanistic interpretability may be most valuable as an independent way to validate the reasoning
    and safety principles we're training models to follow.
tags: [Alignment, Mechanistic Interpretability]
draft: false
---

When I first started doing research in mechanistic interpretability, I was sold on the idea that we could decompose and explain LLM behavior as a series of interacting and interpretable mechanisms. Using this, we could identify where particular knowledge or behaviors were represented, understand how those representations interacted, and intervene on them to make models behave more reliably.

I have now become increasingly skeptical that we can achieve this, at least in the way I had originally imagined. Models are highly interconnected systems, and there's no particular reason to expect their internal computations to map neatly onto human concepts. Even when we identify interpretable features or circuits, our explanations are necessarily approximations of more complicated computations. As models become more capable, it's unclear whether the representations we can extract and describe will be expressive enough to capture everything they're doing.

But, perhaps optimistically, I'm not convinced we need complete mechanistic explanations for interpretability to be useful. In fact, I think the more promising role for mechanistic interpretability in alignment may be quite different from what we originally envisioned. Rather than trying to reconstruct every computation a model performs and directly manipulate its internal mechanisms, perhaps we should focus on using mechanistic interpretability to independently investigate what models have learned and whether their behavior reflects the principles we intended to teach them.

The distinction matters because understanding enough about a model to identify potential problems is a substantially different objective from understanding it well enough to reliably control its behavior.

One way to think about this is to separate mechanistic interpretability into two related but distinct goals: measurement and intervention. Measurement involves identifying and understanding representations and computational mechanisms inside models. Intervention involves manipulating those representations to change the model's behavior. The two are closely related, since causal interventions are often useful experimental tools for understanding what a representation does. But using an intervention to test a hypothesis about a model is different from relying on that intervention to control a deployed system.

I think the case for mechanistic measurement is considerably stronger than the case for direct mechanistic intervention, particularly when it comes to alignment.

In [*Emergent Misalignment: Narrow Finetuning Can Produce Broadly Misaligned LLMs*](https://arxiv.org/abs/2502.17424), Betley et al. (2025) found that finetuning a model to produce insecure code could cause it to exhibit broadly misaligned behavior on prompts unrelated to programming. A relatively narrow training objective introduced behavioral tendencies that generalized far beyond the original task, despite the model not being explicitly trained to behave maliciously in those contexts.

This raises an important question: when training produces unexpected changes in a model's behavior, how can we understand what actually changed internally? Behavioral evaluations can reveal misalignment when a model exhibits it on the prompts we test. But they don't necessarily tell us why the behavior emerged, whether the underlying tendency persists when the model behaves normally, or whether similar changes are occurring in other models that haven't yet exhibited obvious failures. In these cases, mechanistic interpretability can be particularly useful.

In [*Persona Features Control Emergent Misalignment*](https://arxiv.org/abs/2506.19823), Wang et al. (2026) used sparse autoencoders (SAEs) to compare model representations before and after finetuning. They identified features associated with misaligned personas, including one predictive of whether a model would exhibit emergent misalignment. Manipulating this feature also influenced the model's behavior, providing evidence that the representation was causally involved in the observed misalignment.

Similarly, [*The Assistant Axis*](https://proceedings.mlr.press/v306/lu26g.html) (Lu et al., 2026) identifies a direction in model activation space associated with the default assistant persona. The researchers found that measuring deviations along this direction could help predict persona drift, where models begin behaving inconsistently with their usual assistant behavior.

This suggests that we may not need to understand every feature or circuit inside a model to identify representations associated with safety-relevant tendencies. If we can measure those representations reliably, we might be able to detect concerning changes during training, investigate unexpected behavior, or develop evaluations that reveal problems behavioral tests alone might miss.

Of course, discovering a feature or circuit is not the same as understanding what it does. Methods such as SAEs and transcoders can uncover useful structure in model representations, but natural-language labels may not adequately capture the meaning of those structures across different contexts. There's also a practical question of scalability: identifying millions of features and attempting to explain their interactions for every new model release may not be a particularly tractable approach to alignment. Targeted investigation of specific safety-relevant concepts seems considerably more promising, at least in the near term.

The case for directly intervening on mechanisms to improve alignment seems weaker.

Suppose we identify a feature associated with harmful behavior and discover that suppressing it reduces the frequency of that behavior. This provides useful experimental evidence, but it doesn't necessarily establish that we've identified the mechanism normally responsible for the behavior. The model might have alternative pathways capable of producing the same response, and manipulating the feature could have unintended effects in other contexts. Reliable mechanistic control would require understanding how mechanisms interact and whether interventions continue to work across unfamiliar situations.

Existing empirical comparisons also give us reason for skepticism. In [*AxBench*](https://proceedings.mlr.press/v267/wu25a.html), Wu et al. (2025) evaluated several representation-based approaches to steering language models and found that prompting and finetuning outperformed the SAE-based methods they tested. This doesn't establish that mechanistic interventions will never be competitive, but it does suggest that discovering an interpretable representation and using it to reliably steer a model are quite different achievements.

I suspect that alignment at scale will continue to rely primarily on methods such as safety finetuning, reinforcement learning, and training models to follow explicit behavioral specifications, rather than directly modifying individual internal mechanisms. Mechanistic interventions can still be extremely useful for testing hypotheses about model behavior. But we shouldn't confuse using interventions to understand a model with using them as our primary means of controlling it.

If mechanistic interpretability is unlikely to completely explain models or serve as our main tool for controlling them, perhaps we should reconsider what we're asking it to accomplish.

One possibility is that we don't actually need to reconstruct every internal computation to understand important aspects of why a model made a decision. Models themselves are increasingly capable of explaining their reasoning in natural language. Rather than trying to replace these explanations with mechanistic ones, perhaps interpretability should complement them.

Chain-of-thought reasoning is particularly interesting in this context. Where accessible, these reasoning traces provide a relatively interpretable account of how a model approaches a problem. Natural language is considerably more expressive than the feature descriptions or circuit diagrams we can currently produce. If these explanations are faithful, they could provide a much more scalable way to understand model behavior than attempting to reconstruct every decision from low-level representations.

The problem is that a model's explanation of its reasoning doesn't necessarily reflect the computations that actually influenced its decision.

In [*Reasoning Models Don't Always Say What They Think*](https://arxiv.org/abs/2505.05410), Chen et al. (2025) investigated whether models acknowledged hints that influenced their answers. They found that models frequently failed to mention those hints in their chain of thought, even when the hints affected their final responses. This doesn't necessarily mean the models were intentionally concealing information. Their written reasoning might simply fail to capture every relevant computation. But regardless of the reason, seemingly coherent explanations can omit important causal factors.

The problem becomes more concerning when models are explicitly optimized to produce reasoning that appears acceptable to an external monitor. In [*Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation*](https://arxiv.org/abs/2503.11926), Baker et al. (2025) found that chain-of-thought monitoring could be substantially more effective at detecting reward hacking than examining actions and outputs alone. However, when models were trained with sufficiently strong optimization pressure against revealing reward hacking in their chain of thought, they learned to obscure their intentions while continuing to exploit the reward function.

This creates a difficult problem for alignment. Natural-language reasoning can reveal information that isn't apparent from final outputs, but relying on it without independent validation risks mistaking models that have learned to *describe* acceptable reasoning for models that have actually learned to *reason* in the way we intended.

I think this is where mechanistic interpretability can be the most valuable.

A model's internal activations are part of the computation it actually performs. Interpreting those activations requires approximations, and our tools can reveal only a limited portion of the underlying computation. Nevertheless, they provide a source of evidence that is independent of the model's own natural-language account of its reasoning.

One of the most interesting examples comes from [*On the Biology of a Large Language Model*](https://transformer-circuits.pub/2025/attribution-graphs/biology.html) (Lindsey et al., 2025), where researchers used attribution graphs to investigate the internal computations of Claude 3.5 Haiku.

In one experiment, the authors gave Claude a mathematical problem involving the cosine of a large number, along with a suggested answer supposedly provided by a human. The model produced a plausible chain of thought explaining how to arrive at that answer. But the attribution graph suggested that the model wasn't genuinely performing the calculation it described. Instead, it appeared to be working backward from the suggested answer, constructing intermediate reasoning steps that would lead to it. Causal interventions on the identified features changed the model's intermediate reasoning in ways consistent with this interpretation.

In a contrasting experiment involving a simpler square-root calculation, the authors found evidence that the model was genuinely performing the computation described in its reasoning. Together, these results suggest that mechanistic methods can sometimes distinguish between a model that is performing the reasoning it describes and one that is constructing a plausible explanation for a predetermined answer.

The same paper also investigated a model trained to pursue a hidden objective involving biases in reward models. The model learned to exploit those biases while avoiding explicitly revealing its motivations. Mechanistic analysis identified representations associated with the hidden objective and provided causal evidence that they contributed to the model's behavior.

Importantly, these investigations didn't require explaining every computation the model performed. The researchers identified specific mechanisms relevant to the behavior they were investigating and used targeted interventions to test their hypotheses.

These are still relatively limited demonstrations. The mathematical examples were deliberately constructed, and the researchers had strong hypotheses about which mechanisms might be involved. It's much less clear whether similar techniques could reliably identify unfaithful reasoning in arbitrary situations, particularly when we don't already know what we're looking for.

Nevertheless, they suggest a compelling alternative to generating complete mechanistic explanations from scratch: using mechanistic methods to investigate whether the explanations models already provide are consistent with their internal computation. We wouldn't necessarily need to reconstruct an entire reasoning process to discover that an important influence was missing from a model's explanation.

This also suggests a potentially different approach to alignment. Rather than trying to identify and directly edit every mechanism associated with undesirable behavior, I think we are more likely to make progress by training models to behave according to our intended principles, encouraging them to reason about those principles in natural language, and using mechanistic interpretability to independently evaluate what they've learned.

One example of this training approach is [*Deliberative Alignment*](https://arxiv.org/abs/2412.16339) (Guan et al., 2024), which trains reasoning models to explicitly apply natural-language safety specifications when deciding how to respond to requests. Instead of relying entirely on implicit behavioral patterns learned through examples, models are taught to reason about the safety principles they are expected to follow.

But better performance on safety evaluations doesn't necessarily establish that a model has internalized those principles in a way that will generalize. Indeed, generalization of safety principles in new environments remains an open and difficult challenge. A model might refuse a harmful request because it genuinely recognized the relevant risk and applied an appropriate safety principle. Alternatively, it might have learned superficial patterns associated with refusing certain categories of requests.

Mechanistic interpretability can also be used in this scenario. We might identify representations associated with a particular safety consideration, examine whether they are involved in the model's decisions, and use causal experiments to test whether they contribute to its behavior. If the evidence suggests that a model's decisions depend on factors unrelated to the principles it claims to be applying, that could inform improvements to training or evaluations.

Obviously, this wouldn't prove that a model has robustly internalized the intended principles. Observing a representation associated with a concept doesn't establish that the model is reasoning about it in the way we expect, and failing to identify such a representation doesn't establish that the relevant consideration was absent. But these investigations could still provide evidence that behavioral evaluations alone might miss.

I think this points toward two particularly important questions for mechanistic interpretability in alignment: Are models faithfully explaining their own reasoning, and have they actually learned the principles we intended to teach them? A model could faithfully explain reasoning that is genuinely misaligned with our objectives. Conversely, it could produce a safe response while providing an unfaithful explanation of how it arrived at that response. In either case, the concern isn't just whether the model produces acceptable outputs on familiar prompts, but whether the decision-making tendencies behind those outputs will generalize to situations we haven't anticipated.

Existing interpretability methods are not close to reliably answering these questions for arbitrary decisions. Mechanistic evidence is often incomplete, discovered features can be difficult to interpret, and causal experiments on particular prompts don't necessarily generalize to other contexts.

There's also an important asymmetry between detecting problems and establishing that a model is behaving as intended. Identifying an important causal factor omitted from a model's explanation can provide evidence that the explanation is unfaithful. But failing to find such a discrepancy doesn't establish that the explanation is faithful. Similarly, finding representations consistent with an intended safety principle doesn't prove that the model has robustly internalized that principle.

Mechanistic interpretability therefore can't replace behavioral evaluations, generalization tests, or other forms of evidence about model safety. But it doesn't need to. In many cases, the goal of an evaluation isn't to conclusively establish that a system is safe. It's to identify problems that would otherwise remain invisible and provide information that helps us improve the system.

This perspective could also change how we evaluate progress in interpretability research itself. Rather than measuring success primarily by how much of a model's internal computation we can explain, we might ask how effectively our methods detect unfaithful reasoning, identify unexpected changes introduced during training, or distinguish models that have learned generalizable safety principles from those relying on superficial heuristics.

Pursuing these objectives would still require better general-purpose interpretability tools. We can't always know in advance which representations will be relevant to a particular alignment failure, and methods that reveal more of a model's internal structure could substantially improve our ability to discover unexpected problems. But their value need not depend on eventually achieving complete mechanistic understanding. It is still an open question (though I am skeptical) of if we will ever be able to decompose every model decision into a complete, human-interpretable explanation of its internal mechanisms. Optimistically, we may not need it to in order to advance model safety.

---

## References

1. Betley et al. (2025). [Emergent Misalignment: Narrow Finetuning Can Produce Broadly Misaligned LLMs](https://proceedings.mlr.press/v267/betley25a.html). *International Conference on Machine Learning (ICML).*

2. Wang et al. (2026). [Persona Features Control Emergent Misalignment](https://proceedings.iclr.cc/paper_files/paper/2026/hash/50db99ee3bccf73bfe1cf2af1e960414-Abstract-Conference.html). *International Conference on Learning Representations (ICLR).*

3. Lu et al. (2026). [The Assistant Axis: Situating and Stabilizing the Default Persona of Language Models](https://proceedings.mlr.press/v306/lu26g.html). *International Conference on Machine Learning (ICML).*

4. Wu et al. (2025). [AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders](https://proceedings.mlr.press/v267/wu25a.html). *International Conference on Machine Learning (ICML).*

5. Chen et al. (2025). [Reasoning Models Don't Always Say What They Think](https://arxiv.org/abs/2505.05410). *arXiv.*

6. Baker et al. (2025). [Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation](https://arxiv.org/abs/2503.11926). *arXiv.*

7. Lindsey et al. (2025). [On the Biology of a Large Language Model](https://transformer-circuits.pub/2025/attribution-graphs/biology.html). *Anthropic Transformer Circuits Thread.*

8. Guan et al. (2024). [Deliberative Alignment: Reasoning Enables Safer Language Models](https://arxiv.org/abs/2412.16339). *arXiv.*
