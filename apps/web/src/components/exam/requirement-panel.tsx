"use client";
import Link from "next/link";
import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { requirementSpecRows, photographSpecRows } from "../../lib/spec-format";
import { appearanceGuidance, type Verdict } from "../../lib/appearance-rules";
import { specimensFor } from "../../lib/specimens";
import { DocumentWorkspace } from "./document-workspace";
import { RequirementUpload } from "./requirement-upload";
import { SpecimenSheet, Tick, Cross } from "./specimen-sheet";
import { ReportIssue } from "./report-issue";
import { FileTypeDrawing } from "../euk/doodles";
import { useLocale, useTr } from "../locale-context";
import { localValue } from "../../lib/i18n";
import { toolText } from "../../lib/i18n-tool";

/**
 * One file, curated for itself.
 *
 * Every panel speaks the same language: the file's name and what we do to it,
 * its measurements as the notice publishes them, the upload, and beside it the
 * specimen sheet and the rules. What changes is the file. A photograph panel
 * talks about faces, caps and backgrounds; a signature panel about ink and
 * capitals; a document panel about pages. Nothing on a panel is generic advice:
 * the specimens and verdicts come from this examination's own record.
 */

const MEANINGLESS = /^(not_found|unknown|none)$/i;

function meaningful(value?: string | null): string | null {
    return value && !MEANINGLESS.test(value.trim()) ? value : null;
}

function backgroundPhrase(raw: unknown, tr: (english: string, hindi: string) => string): string | null {
    const background = raw as { mode?: string; required_colour?: string } | undefined;
    switch (background?.mode) {
        case "exact_colour": {
            const colour = background.required_colour;
            if (!colour) return tr("the exact colour it asks for", "ठीक वही रंग जो माँगा गया है");
            if (colour.startsWith("#"))
                return colour.toUpperCase() === "#FFFFFF"
                    ? tr("plain white", "सादा सफ़ेद")
                    : tr("the exact colour it asks for", "ठीक वही रंग जो माँगा गया है");
            return tr(`plain ${colour.toLowerCase()}`, `सादा ${colour.toLowerCase()}`);
        }
        case "plain_light":
            return tr("plain and light", "सादा और हल्का");
        case "plain_background":
            return tr("plain", "सादा");
        default:
            return null;
    }
}

function introFor(r: RequirementSummary, exam: ExamDetail, tr: (english: string, hindi: string) => string): string {
    if (r.platform_support === "not_yet_supported")
        return tr(
            "We can’t prepare this file yet. Here is what the notice asks, so you can do it yourself.",
            "यह फ़ाइल हम अभी तैयार नहीं कर सकते। नोटिस में क्या माँगा गया है, वह यहाँ है, ताकि आप खुद कर सकें।",
        );
    if (r.platform_support === "physical_stage")
        return tr(
            "This happens in person, at a later stage. Here is what the notice asks.",
            "यह बाद के चरण में खुद जाकर होता है। नोटिस में क्या माँगा गया है, वह यहाँ है।",
        );
    if (r.platform_support === "guidance_only")
        return r.submission_method === "official_live_capture"
            ? tr(
                  "The portal takes this photograph itself. There is nothing to upload.",
                  "यह फ़ोटो पोर्टल खुद खींचता है। अपलोड करने को कुछ नहीं है।",
              )
            : tr(
                  "This is a step you take yourself. Here is what the notice asks.",
                  "यह काम आपको खुद करना है। नोटिस में क्या माँगा गया है, वह यहाँ है।",
              );

    const partial =
        r.platform_support === "partially_supported"
            ? tr(
                  " One thing it asks for, we can’t add yet. It is named below.",
                  " इसमें माँगी गई एक चीज़ हम अभी नहीं जोड़ सकते। वह नीचे बताई गई है।",
              )
            : "";
    switch (r.requirement_type) {
        case "photograph": {
            const background = backgroundPhrase(
                (exam.image_requirements as Record<string, unknown>)?.background,
                tr,
            );
            return tr(
                `Any clear photo of you will do. We frame it, ${background ? `make the background ${background}, ` : ""}and size it to the rules.${partial}`,
                `आपकी कोई भी साफ़ फ़ोटो चलेगी। हम उसे सही फ़्रेम में रखते हैं, ${background ? `बैकग्राउंड ${background} करते हैं, ` : ""}और नियमों के हिसाब से साइज़ करते हैं।${partial}`,
            );
        }
        case "signature":
            return tr(
                `Sign on plain paper and take a photo of it. We crop to the ink and size it to the rules, without stretching a stroke.${partial}`,
                `सादे काग़ज़ पर हस्ताक्षर करें और उसकी फ़ोटो लें। हम स्याही के हिसाब से काटते हैं और नियमों के हिसाब से साइज़ करते हैं, बिना किसी लकीर को खींचे।${partial}`,
            );
        case "thumb_impression":
            return tr(
                `Press your thumb on plain paper and take a photo of it. We crop to the impression and size it to the rules.${partial}`,
                `सादे काग़ज़ पर अंगूठा लगाएँ और उसकी फ़ोटो लें। हम निशान के हिसाब से काटते हैं और नियमों के हिसाब से साइज़ करते हैं।${partial}`,
            );
        case "handwritten_declaration":
            return tr(
                `Write it out on plain paper and photograph the whole page. We size it to the rules and never crop the page down to the writing.${partial}`,
                `इसे सादे काग़ज़ पर लिखें और पूरे पन्ने की फ़ोटो लें। हम इसे नियमों के हिसाब से साइज़ करते हैं, पन्ने को लिखावट तक कभी नहीं काटते।${partial}`,
            );
        default:
            return tr(
                `Bring the pages as photos or PDFs. Put them in order, leave out what isn’t needed, and we make one file to the rules.${partial}`,
                `पन्ने फ़ोटो या PDF के रूप में लाएँ। उन्हें क्रम में रखें, जो ज़रूरी नहीं उसे हटाएँ, और हम नियमों के हिसाब से एक फ़ाइल बनाते हैं।${partial}`,
            );
    }
}

const GOOD: Record<string, [string, string]> = {
    photograph: ["A good photograph, and what to avoid", "अच्छी फ़ोटो, और किन बातों से बचें"],
    signature: ["A good signature, and what to avoid", "अच्छा हस्ताक्षर, और किन बातों से बचें"],
    thumb_impression: ["A good thumb impression, and what to avoid", "अंगूठे का अच्छा निशान, और किन बातों से बचें"],
    handwritten_declaration: ["A good declaration, and what to avoid", "अच्छी घोषणा, और किन बातों से बचें"],
};

const VERDICT_WORD: Record<Verdict, [string, string]> = {
    prohibited: ["Not allowed", "मना है"],
    conditional: ["Allowed, on a condition", "शर्त के साथ चलेगा"],
    required: ["Required", "ज़रूरी"],
    permitted: ["Allowed", "चलेगा"],
};

function VerdictMark({ verdict }: { verdict: Verdict }) {
    return (
        <span className="euk-verdict-mark" aria-hidden="true">
            {verdict === "prohibited" ? (
                <Cross />
            ) : verdict === "conditional" ? (
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round">
                    <path d="M3 11 C 6 6, 9 6, 10 10 C 11 14, 14 14, 17 9" />
                </svg>
            ) : (
                <Tick />
            )}
        </span>
    );
}

export function RequirementPanel({
    requirement,
    index,
    exam,
    onWorking,
}: {
    requirement: RequirementSummary;
    index: number;
    exam: ExamDetail;
    onWorking?: (value: boolean) => void;
}) {
    const r = requirement;
    const locale = useLocale();
    const tr = useTr();
    const supported =
        r.platform_support === "supported" ||
        r.platform_support === "partially_supported";
    const partial = r.platform_support === "partially_supported";
    const photo = r.requirement_type === "photograph";
    const documents =
        r.requirement_type === "certificate_scan" ||
        r.requirement_type === "identity_document";
    const rows = photo
        ? photographSpecRows(exam)
        : requirementSpecRows(r, index, exam.provenance);
    const guidance = photo ? appearanceGuidance(exam.image_requirements) : [];
    const specimens = supported ? specimensFor(r, exam) : [];
    const instructions = meaningful(r.content_instructions);
    const official = exam.source_evidence.some((s) => s.official_source);
    const rulesHref = `/exam/${exam.exam_id}/rules`;

    return (
        <section
            className={`euk-file euk-file--${r.requirement_type.replace(/_/g, "-")}`}
            aria-label={r.requirement_name}
        >
            <header className="euk-file-head">
                <FileTypeDrawing type={r.requirement_type} className="euk-file-icon" />
                <div className="min-w-0">
                    <h2 className="euk-display euk-file-title">{r.requirement_name}</h2>
                    <p className="euk-file-intro">{introFor(r, exam, tr)}</p>
                </div>
            </header>

            {r.requirement_status === "conditional" && meaningful(r.applicability) && (
                <p className="euk-file-when">
                    <strong>{tr("Only if it applies to you.", "सिर्फ़ तभी, जब यह आप पर लागू हो।")}</strong> {r.applicability}
                </p>
            )}

            {!supported ? (
                <div className="euk-file-self">
                    <p>
                        {instructions ||
                            meaningful(r.notes) ||
                            tr("Complete this requirement through the examination’s official instructions.", "यह काम परीक्षा के आधिकारिक निर्देशों के अनुसार पूरा करें।")}
                    </p>
                    {r.rejection_conditions.length > 0 && (
                        <>
                            <h3 className="euk-file-h3">{tr("What the notice says gets rejected", "नोटिस के अनुसार क्या अस्वीकार होता है")}</h3>
                            <ul>
                                {r.rejection_conditions.map((condition) => (
                                    <li key={condition}>{condition}</li>
                                ))}
                            </ul>
                        </>
                    )}
                    <Link className="euk-link" href={rulesHref}>
                        {tr("Read the examination’s sources", "परीक्षा के स्रोत पढ़ें (अंग्रेज़ी में)")}
                    </Link>
                </div>
            ) : (
                <div className="euk-file-grid">
                    <div className="euk-file-work">
                        <div className="euk-file-work-inner">
                        {rows.length > 0 && (
                            <dl
                                className="euk-measure"
                                aria-label={tr(`${r.requirement_name} specification`, `${r.requirement_name} के नियम`)}
                            >
                                {rows.map((row) => (
                                    <div key={row.term} className="euk-measure-cell">
                                        <dt>{toolText(locale, row.term)}</dt>
                                        <dd>
                                            {localValue(locale, row.value)}
                                            {row.estimated && (
                                                <abbr
                                                    title={tr(
                                                        "Platform estimate: this value has not been established by an official source.",
                                                        "हमारा अनुमान: यह मान किसी आधिकारिक स्रोत से तय नहीं हुआ है।",
                                                    )}
                                                >
                                                    {" "}
                                                    {tr("est.", "अनुमानित")}
                                                </abbr>
                                            )}
                                        </dd>
                                    </div>
                                ))}
                            </dl>
                        )}
                        {partial && (
                            <div className="euk-file-partial">
                                <p className="euk-file-partial-title">{tr("One step stays yours", "एक काम आपका रहेगा")}</p>
                                <p>
                                    {toolText(locale, guidance.find((g) => g.id === "imprint")?.detail ?? "") ||
                                        meaningful(r.notes) ||
                                        tr("Check the examination’s instructions before submitting.", "जमा करने से पहले परीक्षा के निर्देश देख लें।")}
                                </p>
                            </div>
                        )}
                        {documents ? (
                            <DocumentWorkspace
                                onWorking={onWorking}
                                examId={exam.exam_id}
                                examName={exam.exam_name}
                                requirementId={r.requirement_id}
                                requirementName={r.requirement_name}
                                partiallySupported={partial}
                            />
                        ) : (
                            <RequirementUpload
                                onWorking={onWorking}
                                examId={exam.exam_id}
                                examName={exam.exam_name}
                                requirementId={r.requirement_id}
                                requirementName={r.requirement_name}
                                requirementType={r.requirement_type}
                                partiallySupported={partial}
                            />
                        )}
                        </div>
                    </div>

                    <div className="euk-file-guide">
                        {specimens.length > 0 && (
                            <>
                                <h3 className="euk-file-h3">
                                    {GOOD[r.requirement_type]
                                        ? tr(GOOD[r.requirement_type][0], GOOD[r.requirement_type][1])
                                        : tr("A good document, and what to avoid", "अच्छा दस्तावेज़, और किन बातों से बचें")}
                                </h3>
                                <SpecimenSheet
                                    locale={locale}
                                    specimens={specimens}
                                    note={tr(
                                        `Drawn to show each rule. Marked from ${exam.conducting_body}’s published rules and the checks we run on every upload.`,
                                        `हर नियम दिखाने के लिए बनाया गया। ${exam.conducting_body} के प्रकाशित नियमों और हर अपलोड पर हमारी जाँच के आधार पर।`,
                                    )}
                                />
                            </>
                        )}

                        {guidance.length > 0 && (
                            <>
                                <h3 className="euk-file-h3">{tr("What the notice says about how you look", "आप कैसे दिखें, इस पर नोटिस क्या कहता है")}</h3>
                                <ul className="euk-verdicts">
                                    {guidance.map((g) => (
                                        <li key={g.id} className={`euk-verdict euk-verdict--${g.verdict}`}>
                                            <VerdictMark verdict={g.verdict} />
                                            <div className="min-w-0">
                                                <p className="euk-verdict-title">
                                                    {toolText(locale, g.title)}{" "}
                                                    <span className="euk-verdict-word">
                                                        {tr(VERDICT_WORD[g.verdict][0], VERDICT_WORD[g.verdict][1])}
                                                    </span>
                                                </p>
                                                <p>{toolText(locale, g.detail)}</p>
                                                {g.sourceWording && (
                                                    <p className="euk-verdict-quote">
                                                        {tr("The notice", "नोटिस")}: “{g.sourceWording}”
                                                    </p>
                                                )}
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}

                        <div className="euk-file-mores">
                            {instructions && (
                                <details className="euk-file-more">
                                    <summary>{tr("How the notice says to prepare it", "नोटिस के अनुसार इसे कैसे तैयार करें")}</summary>
                                    <p>{instructions}</p>
                                </details>
                            )}
                            <details className="euk-file-more">
                                <summary>{tr("What may be rejected", "क्या अस्वीकार हो सकता है")}</summary>
                                <h4>{tr("By the examination authority", "परीक्षा संस्था द्वारा")}</h4>
                                {r.rejection_conditions.length ? (
                                    <ul>
                                        {r.rejection_conditions.map((condition) => (
                                            <li key={condition}>{condition}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p>
                                        {tr(
                                            "No specific rejection conditions are recorded for this file. Check the linked source.",
                                            "इस फ़ाइल के लिए अस्वीकृति की कोई ख़ास शर्त दर्ज नहीं है। दिए गए स्रोत को देखें।",
                                        )}
                                    </p>
                                )}
                                <h4>{tr("When we can’t prepare a file", "जब हम फ़ाइल तैयार नहीं कर पाते")}</h4>
                                <p>
                                    {photo
                                        ? tr(
                                              "We need a readable image with one clear, detectable face. Anything else we notice is shown for you to review.",
                                              "हमें एक साफ़ फ़ोटो चाहिए जिसमें एक चेहरा साफ़ पहचाना जा सके। और कुछ भी दिखे तो वह आपको जाँचने के लिए दिखाया जाता है।",
                                          )
                                        : tr(
                                              "We need a readable file. We’ll tell you if we can’t prepare it or can’t meet a specification.",
                                              "हमें पढ़ने लायक फ़ाइल चाहिए। अगर हम उसे तैयार न कर पाएँ या कोई नियम पूरा न हो, तो हम बताएँगे।",
                                          )}
                                </p>
                            </details>
                        </div>

                        <p className="euk-file-sources">
                            <Link href={rulesHref}>
                                {official
                                    ? tr("View the examination’s sources", "परीक्षा के स्रोत देखें (अंग्रेज़ी में)")
                                    : tr("View the sources we found", "हमें मिले स्रोत देखें (अंग्रेज़ी में)")}
                            </Link>
                            <ReportIssue
                                examName={exam.exam_name}
                                requirementName={r.requirement_name}
                                ruleId={exam.rule_id}
                            />
                        </p>
                    </div>
                </div>
            )}
        </section>
    );
}
