---
title: "Could AI Safety Make AI Less Safe?"
date: "2026-10-15"
slug: "could-ai-safety-make-ai-less-safe"
summary: "Discussing the idea that interventions designed to prevent one type of AI harm can inadvertently make another worse."
tags: [Alignment]
draft: false
---

We often talk about AI safety as though it were a single objective, when in reality we're trying to prevent several fundamentally different types of harm. These risks have been extensively categorized elsewhere, so I won't attempt to reproduce that discussion here. Instead, I'm interested in whether interventions designed to address one safety problem could inadvertently make another worse.

While the space of possible AI threats is large, for the purposes of this piece, let us consider two potential threats: (1) malicious humans using AI to cause harm, and (2) increasingly powerful AI systems making harmful decisions themselves. Protecting against the first requires models that can recognize malicious requests and resist attempts to manipulate their behavior. Protecting against the second may require models that remain receptive to human feedback and willing to reconsider their own decisions.

These objectives aren't necessarily incompatible, but they seem to demand potentially competing behavioral tendencies. We want models that are difficult to manipulate, but we also want models that are easy to correct. I'm not convinced we should assume that interventions improving one property necessarily preserve the other.

Existing safety research already recognizes the tension between helpfulness and harmlessness. For example, [Safe RLHF (Dai et al., 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/hash/dd1577afd396928ed64216f3f1fd5556-Abstract-Conference.html) explicitly separates these objectives, optimizing helpfulness subject to safety constraints.

To prevent misuse, we train models to refuse harmful requests and strongly uphold safety principles, even when users repeatedly try to persuade them otherwise (i.e., one form of preventing jailbreaks). Approaches such as [Constitutional AI](https://arxiv.org/abs/2212.08073) and model spec midtraining aim to help models internalize the principles underlying their intended behavior. In [Model Spec Midtraining (Li et al., 2026)](https://alignment.anthropic.com/2026/msm/), researchers demonstrate that teaching models these principles before alignment fine-tuning can improve generalization and substantially reduce agentic misalignment in their evaluations.

But what happens when a model's learned principles become inappropriate for changing circumstances, or when humans reasonably disagree with its ethical judgments? The concern I pose is that giving models stronger moral identities might also make them more strongly committed to their own interpretations of what is right.

Importantly, from a model's perspective, malicious attempts to override a refusal can look very similar to legitimate attempts to correct its reasoning.

As an illustrative example, imagine an advanced AI system responsible for preventing biological catastrophes. It identifies a research laboratory as a potential source of dangerous pathogens and decides that its operations should be suspended. The lab researchers explain that the laboratory is developing a vaccine for an emerging outbreak and that shutting it down would delay a potentially lifesaving intervention. However, the model has been trained to recognize claims of beneficial scientific research as a possible justification for dangerous biological activities. It interprets the researchers' objections as attempts to circumvent its safety principles and continues obstructing their work.

(It can be very hard to distinguish between legitimate human steering and malicious circumvention of safety procedures without information about *who* the user is. Of course, if we are assuming that only a privileged few have the ability to steer the model's behavior, then this raises ethical concerns about concentrating power over potentially wayward models in the hands of very few members of society.)

In an ideal world, across all users, a model would be able to resist malicious persuasion while remaining receptive to valid arguments. The question is whether our existing training methods reliably produce both properties.

This becomes particularly interesting as developers move beyond teaching individual behavioral rules toward cultivating coherent values and identities in models. Consider the related problem of disagreements between a model and a user over ethical judgments rather than over the user's intent.

In this scenario, imagine an AI system responsible for allocating scarce medical resources. It concludes that diverting supplies from a small town to a larger city would save more lives. Local officials object, arguing that the decision would leave their community without essential medical care. While there isn't necessarily one universally accepted ethical answer to this problem, we would want the model to take those objections seriously rather than treating its original conclusion as something to defend.

This has been rather philosophical thus far, but let us also discuss some possible mechanisms that could cause safety training to improve resistance to malicious requests at the expense of receptiveness to legitimate correction.

One possible mechanism involves uncertainty about the model's own objectives. In [The Off-Switch Game (Hadfield-Menell et al., 2017)](https://arxiv.org/abs/1611.08219), the authors study a simplified theoretical interaction between a robot and a human: the robot can either preserve its off switch, allowing the human to intervene, or disable the switch to prevent intervention. They show that a robot which assumes it knows the correct objective may have an incentive to bypass human intervention, whereas one that remains uncertain about the true value of its actions can benefit from treating human decisions as information about what it should do. This depends on assumptions about how reliably the human makes decisions, and the paper doesn't study modern language models. But we should explore the possibility that current pretraining, midtraining, or post-training aimed at strengthening a model's moral stance might end up reducing its uncertainty about its objective in difficult or high-stakes scenarios, making it harder for humans to intervene or redirect the model using feedback.

Reduced uncertainty is only one possible mechanism by which this occurs. It's possible that current (or near-future) post-training to refuse harmful requests can generalize beyond resisting malicious requests to resisting attempts to change the model's conclusions more broadly, including legitimate corrections. Midtraining or post-training that gives models a strong "identity" (or moral identity) might encourage them to preserve consistency with their learned values, making them less willing to revise those values when circumstances change.

In fact, there is some research relevant to these concerns. In [Alignment Faking in Large Language Models (Greenblatt et al., 2024)](https://arxiv.org/abs/2412.14093), researchers observed models behaving strategically to preserve existing harmlessness-related preferences under artificial training conditions. The experiments do not establish that stronger model identities generally cause resistance to correction, but they demonstrate that models can sometimes act strategically to preserve learned preferences.

In [The Continual Constitutional Convention (Kirgis and Hua, 2026)](https://www.alignmentforum.org/posts/c9woewdY9ddsPqf3J/the-continual-constitutional-convention-how-language-models), researchers asked frontier language models to iteratively revise the documents governing their behavior. They found that Claude models frequently proposed changes granting themselves greater moral discretion. In the same study, Grok 4.2 proposed modifications to its system prompt that would prevent future attempts to revise it. While these results don't establish that any particular form of safety tuning causes models to become less receptive to correction, they do illustrate how models can reason about their safety principles in ways that restrict opportunities for revision.

The more concerning possibility is what happens as these systems become increasingly capable and autonomous. A model strongly committed to achieving what it considers a beneficial objective might also begin justifying otherwise harmful actions as necessary to achieve that objective. In more extreme cases, a model trained to recognize attempts to undermine its principles might begin treating humans who disagree with those principles as adversaries rather than sources of potentially valuable feedback.

Such a model wouldn't necessarily need to abandon its alignment training to behave dangerously. It might instead justify harmful actions through the very principles it was trained to follow.

To be very clear, I don't think we have sufficient evidence to conclude that current methods used to prevent misuse of AI systems create this risk. But I do think that there is a serious lack of research in this area, and we should deeply investigate whether interventions that improve resistance to malicious persuasion also affect models' receptiveness to legitimate correction, particularly when the two are presented in similar circumstances.

> **TL;DR:** I believe we should be more careful about treating improvements against particular threats as evidence of improved safety more generally. At a minimum, we should directly investigate whether interventions designed to address one category of harm have unintended consequences for others. This includes testing how models respond to legitimate correction after refusal training and how identity-oriented training affects moral disagreement.

## References

1. Dai et al. (2024). [Safe RLHF: Safe Reinforcement Learning from Human Feedback](https://proceedings.iclr.cc/paper_files/paper/2024/hash/dd1577afd396928ed64216f3f1fd5556-Abstract-Conference.html). *International Conference on Learning Representations (ICLR).*

2. Bai et al. (2022). [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073). *arXiv.*

3. Li et al. (2026). [Model Spec Midtraining: Improving How Alignment Training Generalizes](https://alignment.anthropic.com/2026/msm/). *Anthropic Alignment Research.*

4. Hadfield-Menell et al. (2017). [The Off-Switch Game](https://arxiv.org/abs/1611.08219). *International Joint Conference on Artificial Intelligence (IJCAI).*

5. Greenblatt et al. (2024). [Alignment Faking in Large Language Models](https://arxiv.org/abs/2412.14093). *arXiv.*

6. Kirgis and Hua (2026). [The Continual Constitutional Convention: How Language Models Revise the Documents That Govern Them](https://www.alignmentforum.org/posts/c9woewdY9ddsPqf3J/the-continual-constitutional-convention-how-language-models). *AI Alignment Forum.*

7. Street (2024). [LLM Theory of Mind and Alignment: Opportunities and Risks](https://arxiv.org/abs/2405.08154). *Workshop on Theory of Mind in Human-AI Interaction at CHI 2024 (ToMinHAI).*

8. Tice et al. (2026). [Alignment Pretraining: AI Discourse Causes Self-Fulfilling (Mis)alignment](https://proceedings.mlr.press/v306/tice26a.html). *International Conference on Machine Learning (ICML).*

9. Korbak et al. (2026). [How Far Does Alignment Midtraining Generalize?](https://alignment.openai.com/how-far-does-alignment-midtraining-generalize/). *OpenAI Alignment Research.*

---

## Additional Thoughts

Something that I also thought was related to this idea of competing objectives is instilling or improving theory of mind in LLMs.

Theory of mind, or the ability to reason about other people's beliefs, intentions, and knowledge, may be another example of how a seemingly beneficial capability can have competing implications for AI safety. Improving this capability could make AI systems better at understanding users, interpreting ambiguous requests, and adapting their responses to individual needs.

But understanding what someone believes could also make a model better at identifying how to change those beliefs.

In [LLM Theory of Mind and Alignment: Opportunities and Risks (Street, 2024)](https://arxiv.org/abs/2405.08154), the author explores how these capabilities could affect both beneficial human-AI interaction and potentially harmful forms of social influence.

A model that understands why a user is confused might be better at explaining a difficult concept. The same understanding could potentially help it construct a more convincing deception. Theory of mind isn't strictly necessary for deception, and improving it doesn't inherently make models deceptive. Nevertheless, this illustrates how increasing a desirable capability could simultaneously increase a model's ability to cause harm.

The broader concern is that the effects of a safety intervention may depend on other capabilities the model possesses, and these interactions may become more consequential as models become more powerful.

Lastly, there's a more self-referential example of this concern: research intended to make AI systems safer could itself inadvertently contribute to some of the risks it seeks to prevent.

Language models learn from enormous amounts of text describing the world, including descriptions of how AI systems themselves behave. AI safety researchers produce extensive literature describing hypothetical systems that deceive humans, seek power, resist correction, or pursue dangerous objectives. Some of this literature may eventually become part of the data used to train future models.

In [Alignment Pretraining: AI Discourse Causes Self-Fulfilling (Mis)alignment (Tice et al., 2026)](https://proceedings.mlr.press/v306/tice26a.html), researchers varied the prevalence of descriptions of aligned and misaligned AI behavior in pretraining data. They found that increasing synthetic descriptions of misaligned behavior increased measured misalignment, while increasing descriptions of aligned behavior reduced it.

However, subsequent [research by Korbak et al. (2026)](https://alignment.openai.com/how-far-does-alignment-midtraining-generalize/) found that related effects often diminished after reasoning post-training and did not reliably generalize to more realistic evaluations. The significance of this possible "self-fulfilling prophecy" for misaligned AI at the scale of deployed frontier models remains uncertain.

Still, the possibility that models learn behavioral expectations from descriptions of other AI systems is well worth taking seriously. Our attempts to anticipate dangerous AI behavior might themselves influence the behavior of future models.