import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {CaptionOverlay, WordCaption} from "./components/CaptionOverlay";
import {resolveAsset} from "./lib/resolveAsset";

export type FastbullSfxCue = {src: string; atSeconds: number; volume?: number};
export type FastbullInsertCue = {type: "video" | "image" | "motion_card"; atSeconds: number; durationSeconds: number; src?: string; label?: string};

export type FastbullTalkingHeadProps = {
  [key: string]: unknown;
  videoSrc: string;
  captions: WordCaption[];
  headline?: string;
  eyebrow?: string;
  pageName?: string;
  cta?: string;
  ctaStartSeconds?: number;
  wordsPerPage?: number;
  fontSize?: number;
  sfx?: FastbullSfxCue[];
  captionWordSeparator?: string;
  inserts?: FastbullInsertCue[];
};

const FONT = '"Fastbull Thai", "Leelawadee UI", Tahoma, sans-serif';
const NAVY = "#071426";
const GOLD = "#D7B56D";
const IVORY = "#FFF8EA";

const Header: React.FC<{headline: string; eyebrow: string}> = ({headline, eyebrow}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = spring({frame, fps, config: {damping: 18, stiffness: 110}});
  const opacity = interpolate(frame, [0, 8, 75, 90], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return <div style={{position: "absolute", top: 132, left: 72, right: 120,
    opacity, transform: `translateY(${(1 - entrance) * -24}px)`, fontFamily: FONT}}>
    <div style={{display: "inline-flex", background: NAVY, borderLeft: `8px solid ${GOLD}`,
      color: GOLD, padding: "9px 18px", fontSize: 25, fontWeight: 700, letterSpacing: 2}}>
      {eyebrow.toUpperCase()}
    </div>
    <div style={{marginTop: 13, color: IVORY, fontSize: 70, fontWeight: 850, lineHeight: 1.14,
      textShadow: "0 4px 18px rgba(0,0,0,.75)", maxWidth: 870}}>{headline}</div>
    <div style={{marginTop: 18, width: Math.max(90, entrance * 420), height: 5,
      background: `linear-gradient(90deg, ${GOLD}, transparent)`}} />
  </div>;
};

const FollowCard: React.FC<{pageName: string; cta: string}> = ({pageName, cta}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 16, stiffness: 130}});
  return <div style={{position: "absolute", left: 64, right: 64, bottom: 250,
    transform: `translateY(${(1 - enter) * 80}px) scale(${0.94 + enter * 0.06})`, opacity: enter,
    background: "rgba(7,20,38,.94)", border: `2px solid ${GOLD}`, borderRadius: 26,
    boxShadow: "0 20px 60px rgba(0,0,0,.45)", padding: "25px 30px", display: "flex",
    alignItems: "center", justifyContent: "space-between", fontFamily: FONT}}>
    <div><div style={{color: GOLD, fontSize: 25, fontWeight: 750}}>FASTBULL</div>
      <div style={{color: IVORY, fontSize: 34, fontWeight: 800}}>{pageName}</div></div>
    <div style={{background: GOLD, color: NAVY, fontSize: 28, fontWeight: 850,
      borderRadius: 999, padding: "15px 25px"}}>+ {cta}</div>
  </div>;
};

const Insert: React.FC<{cue: FastbullInsertCue}> = ({cue}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const fade = Math.min(
    interpolate(frame, [0, Math.min(8, durationInFrames / 3)], [0, 1], {extrapolateRight: "clamp"}),
    interpolate(frame, [Math.max(0, durationInFrames - 8), durationInFrames], [1, 0], {extrapolateLeft: "clamp"}),
  );
  if (cue.type === "motion_card" || !cue.src) {
    const enter = spring({frame, fps, config: {damping: 18, stiffness: 120}});
    return <AbsoluteFill style={{justifyContent: "center", alignItems: "center", background: "rgba(7,20,38,.83)", opacity: fade}}>
      <div style={{width: "82%", borderTop: `5px solid ${GOLD}`, borderBottom: `1px solid ${GOLD}`,
        padding: "42px 24px", color: IVORY, fontFamily: FONT, fontSize: 54, fontWeight: 800,
        lineHeight: 1.25, textAlign: "center", transform: `scale(${0.92 + enter * 0.08})`}}>{cue.label}</div>
    </AbsoluteFill>;
  }
  return <AbsoluteFill style={{opacity: fade}}>
    {cue.type === "video" ? <OffthreadVideo muted src={resolveAsset(cue.src)} style={{width: "100%", height: "100%", objectFit: "cover"}} />
      : <Img src={resolveAsset(cue.src)} style={{width: "100%", height: "100%", objectFit: "cover"}} />}
    <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(7,20,38,.12), rgba(7,20,38,.32))"}} />
  </AbsoluteFill>;
};

export const FastbullTalkingHead: React.FC<FastbullTalkingHeadProps> = ({
  videoSrc, captions, headline = "", eyebrow = "FASTBULL INSIGHT", pageName = "FASTBULL",
  cta = "กดติดตาม", ctaStartSeconds, wordsPerPage = 4, fontSize = 54, sfx = [],
  captionWordSeparator = "",
  inserts = [],
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const ctaFrom = Math.max(0, Math.round((ctaStartSeconds ?? Math.max(0, durationInFrames / fps - 2.7)) * fps));
  const progress = durationInFrames > 1 ? frame / (durationInFrames - 1) : 0;
  return <AbsoluteFill style={{backgroundColor: NAVY, fontFamily: FONT}}>
    <style>{`@font-face{font-family:'Fastbull Thai';src:url('${staticFile("fonts/NotoSansThai-Variable.ttf")}') format('truetype');font-weight:100 900;font-style:normal;}`}</style>
    <OffthreadVideo src={resolveAsset(videoSrc)} style={{width: "100%", height: "100%", objectFit: "cover"}} />
    <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(7,20,38,.33) 0%, transparent 30%, transparent 67%, rgba(7,20,38,.42) 100%)"}} />
    {inserts.map((cue, index) => <Sequence key={`insert-${index}`} from={Math.max(0, Math.round(cue.atSeconds * fps))}
      durationInFrames={Math.max(1, Math.round(cue.durationSeconds * fps))}><Insert cue={cue} /></Sequence>)}
    {headline ? <Header headline={headline} eyebrow={eyebrow} /> : null}
    <CaptionOverlay words={captions} wordsPerPage={wordsPerPage} fontSize={fontSize}
      color={IVORY} highlightColor={GOLD} backgroundColor="rgba(7,20,38,.88)"
      fontFamily={FONT} wordSeparator={captionWordSeparator} bottomPadding={390} maxWidthPercent={86}
      borderColor="rgba(215,181,109,.75)" borderWidth={2} borderRadius={18}
      boxShadow="0 14px 45px rgba(0,0,0,.4)" />
    {ctaFrom < durationInFrames ? <Sequence from={ctaFrom} durationInFrames={durationInFrames - ctaFrom}>
      <FollowCard pageName={pageName} cta={cta} />
    </Sequence> : null}
    {sfx.map((cue, i) => <Sequence key={`${cue.src}-${i}`} from={Math.max(0, Math.round(cue.atSeconds * fps))}>
      <Audio src={resolveAsset(cue.src)} volume={cue.volume ?? 0.25} />
    </Sequence>)}
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 8, background: "rgba(255,255,255,.13)"}}>
      <div style={{width: `${progress * 100}%`, height: "100%", background: GOLD}} />
    </div>
  </AbsoluteFill>;
};
