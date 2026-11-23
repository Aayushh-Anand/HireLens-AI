import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, CheckCircle2, CircleAlert, FileText, FileUp, Gauge, LoaderCircle, RotateCcw, Sparkles, Target, Upload, X, Zap, Lightbulb, ShieldCheck } from 'lucide-react'

const API_URL = 'http://127.0.0.1:8000'
const MAX_FILE_SIZE = 5 * 1024 * 1024
const cx = (...classes) => classes.filter(Boolean).join(' ')

function errorMessage(data, fallback) {
  if (typeof data?.detail === 'string') return data.detail
  if (Array.isArray(data?.detail)) return data.detail.map((item) => item.msg).join(', ')
  return fallback
}
function skillsFrom(result, keys) {
  for (const key of keys) if (Array.isArray(result?.[key])) return result[key].map((item) => typeof item === 'string' ? { name: item } : item)
  return []
}
function skillName(item) { return typeof item === 'string' ? item : item?.name || item?.skill || item?.required_skill || 'Skill' }
function Card({ title, icon: Icon, count, children, className = '' }) {
  return <section className={cx('rounded-3xl border border-slate-200/80 bg-white shadow-[0_12px_45px_-32px_rgba(24,33,62,.28)]', className)}>
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-4 sm:px-6">
      <div className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-lens-lavender/35 text-lens-ink"><Icon size={18}/></span><h3 className="font-bold tracking-tight text-lens-ink">{title}</h3></div>
      {count !== undefined && <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">{count}</span>}
    </div>
    <div className="p-5 sm:p-6">{children}</div>
  </section>
}
function Pill({ children, tone = 'neutral' }) {
  const tones = { matched: 'border-emerald-200 bg-emerald-50 text-emerald-800', missing: 'border-rose-200 bg-rose-50 text-rose-800', neutral: 'border-slate-200 bg-slate-50 text-slate-700' }
  return <span className={cx('inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium', tones[tone])}>{tone === 'matched' && <Check size={13}/>}{tone === 'missing' && <X size={13}/>}{children}</span>
}
function Splash() {
  return <div className="grid min-h-screen place-items-center bg-[#fbfaff] px-5" role="status" aria-label="Loading HireLens AI"><div className="flex flex-col items-center"><img src="/logo.png" alt="HireLens AI" className="w-[min(480px,82vw)] object-contain"/><div className="mt-8 h-1.5 w-44 overflow-hidden rounded-full bg-lens-lavender/40"><div className="h-full w-1/2 animate-pulse rounded-full bg-lens-chartreuse"/></div><p className="mt-4 text-sm font-medium tracking-wide text-slate-500">A clearer view of your next move.</p></div></div>
}
export default function App() {
  const [showSplash, setShowSplash] = useState(true)
  const [file, setFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('matched')
  const fileInputRef = useRef(null)

  useEffect(() => { const timer = window.setTimeout(() => setShowSplash(false), 1000); return () => window.clearTimeout(timer) }, [])

  const chooseFile = (selected) => {
    setError(''); setResult(null)
    if (!selected) return
    const extension = selected.name.split('.').pop()?.toLowerCase()
    if (!['pdf', 'docx'].includes(extension)) { setFile(null); setError('Please upload a PDF or DOCX resume.'); return }
    if (selected.size > MAX_FILE_SIZE) { setFile(null); setError('File size must be 5 MB or less.'); return }
    if (!selected.size) { setFile(null); setError('The selected file is empty.'); return }
    setFile(selected)
  }
  const handleAnalyze = async (event) => {
    event.preventDefault(); setError(''); setResult(null)
    if (!file) { setError('Upload your resume before starting the analysis.'); return }
    if (jobDescription.trim().length < 30) { setError('Please enter a job description with at least 30 characters.'); return }
    if (jobDescription.trim().length > 15000) { setError('The job description cannot exceed 15,000 characters.'); return }
    const formData = new FormData(); formData.append('file', file); formData.append('job_description', jobDescription.trim()); setLoading(true)
    try {
      const response = await fetch(`${API_URL}/analyze`, { method: 'POST', body: formData })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(errorMessage(data, `Analysis failed (${response.status}).`))
      setResult(data); setActiveTab('matched')
    } catch (err) { setError(err.message || 'Could not connect to the backend. Check that FastAPI is running.') }
    finally { setLoading(false) }
  }
  const reset = () => { setResult(null); setError(''); setActiveTab('matched') }

  if (showSplash) return <Splash />

  const matching = result?.matching_result || {}
  const matched = skillsFrom(matching, ['matched_required_skills', 'matched_skills', 'matched'])
  const missing = skillsFrom(matching, ['missing_required_skills', 'missing_skills', 'missing'])
  const preferred = skillsFrom(matching, ['matched_preferred_skills', 'matched_optional_skills'])
  const missingPreferred = skillsFrom(matching, ['missing_preferred_skills', 'missing_optional_skills'])
  const suggestions = Array.isArray(result?.semantic_suggestions) ? result.semantic_suggestions : []
  const quality = result?.resume_quality || {}
  const keyword = result?.keyword_analysis || {}
  const scoreValue = matching.compatibility_score ?? matching.match_score ?? matching.score ?? result?.compatibility_score
  const score = Number.isFinite(Number(scoreValue)) ? Math.max(0, Math.min(100, Number(scoreValue))) : null
  const metrics = Array.isArray(quality.performance_metrics) ? quality.performance_metrics : []
  const strengths = Array.isArray(quality.top_strengths) ? quality.top_strengths : []
  const improvements = Array.isArray(quality.main_improvements) ? quality.main_improvements : []
  const matchedKeywords = keyword.matched_keywords || keyword.matched_required_keywords || []
  const missingKeywords = keyword.missing_keywords || keyword.missing_required_keywords || []
  const keywordCoverage = keyword.coverage_percentage ?? keyword.keyword_coverage_percentage ?? keyword.coverage_score
  const tabs = [{ id: 'matched', label: 'Matched', count: matched.length }, { id: 'missing', label: 'Missing', count: missing.length }, { id: 'preferred', label: 'Preferred', count: preferred.length + missingPreferred.length }]
  const scoreText = score === null ? 'Score unavailable' : score >= 80 ? 'Strong skill coverage' : score >= 60 ? 'Good starting point' : score >= 40 ? 'Room to improve' : 'More skill alignment needed'

  return <div className="min-h-screen bg-[#faf9fd] text-lens-ink">
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <a href="#home" onClick={reset} aria-label="HireLens AI home" className="shrink-0 rounded-xl"><img src="/logo.png" alt="HireLens AI" className="h-12 w-auto max-w-[205px] object-contain object-left sm:h-14"/></a>
        <nav className="hidden items-center gap-7 text-sm font-semibold text-slate-600 md:flex"><a className="transition hover:text-lens-ink" href="#analyzer">Analyzer</a><a className="transition hover:text-lens-ink" href="#how-it-works">How it works</a></nav>
        <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-600 sm:flex"><span className="size-2 rounded-full bg-emerald-500"/> Resume intelligence</div>
      </div>
    </header>

    <main id="home" className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
      <section className="relative overflow-hidden pb-10 pt-14 sm:pb-14 sm:pt-20">
        <div className="pointer-events-none absolute -right-24 -top-20 size-80 rounded-full bg-lens-lavender/25 blur-3xl"/><div className="pointer-events-none absolute right-40 top-48 size-36 rounded-full bg-lens-chartreuse/25 blur-3xl"/>
        <div className="relative max-w-3xl"><div className="inline-flex items-center gap-2 rounded-full border border-lens-lavender/60 bg-white px-3.5 py-2 text-xs font-extrabold tracking-[.12em] text-lens-ink"><Sparkles size={14}/> AI-POWERED CAREER TOOL</div>
          <h1 className="mt-6 text-4xl font-black leading-[1.08] tracking-[-.045em] sm:text-6xl lg:text-7xl">Make your next move<br/><span className="relative inline-block">with clarity.<span className="absolute -bottom-1 left-0 -z-10 h-3 w-full rounded-full bg-lens-chartreuse"/></span></h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg sm:leading-8">Compare your resume with a job description, discover skill gaps, and find relevant experience worth highlighting.</p>
          <div className="mt-7 flex flex-wrap gap-x-5 gap-y-3 text-sm font-semibold text-slate-700"><span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-600"/> Resume analysis</span><span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-600"/> Skill gap insights</span><span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-600"/> Evidence suggestions</span></div>
        </div>
      </section>

      <section id="analyzer" className="scroll-mt-24">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-extrabold tracking-[.16em] text-slate-500">YOUR WORKSPACE</p><h2 className="mt-2 text-2xl font-black tracking-tight sm:text-3xl">Resume analyzer</h2><p className="mt-2 text-sm text-slate-600 sm:text-base">Start with your resume and the role you're targeting.</p></div>{result && <button onClick={reset} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold transition hover:border-slate-300 hover:bg-slate-50"><RotateCcw size={15}/> New analysis</button>}</div>
        <form onSubmit={handleAnalyze} className="grid gap-5 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"><div className="mb-6 flex items-center gap-3"><span className="grid size-11 place-items-center rounded-2xl bg-lens-lavender/40 text-sm font-black">01</span><div><h3 className="font-extrabold">Your resume</h3><p className="mt-1 text-sm text-slate-500">Upload a PDF or DOCX document.</p></div></div>
            <input ref={fileInputRef} type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" className="sr-only" onChange={(event) => { chooseFile(event.target.files?.[0]); event.target.value = '' }}/>
            <div role="button" tabIndex={0} aria-label="Choose resume file" onClick={() => fileInputRef.current?.click()} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); fileInputRef.current?.click() } }} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]) }} className={cx('flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-5 py-8 text-center transition', dragging ? 'border-lens-ink bg-lens-lavender/15' : file ? 'border-emerald-300 bg-emerald-50/60' : 'border-slate-200 bg-slate-50/70 hover:border-lens-lavender hover:bg-lens-lavender/10')}>
              <span className={cx('grid size-14 place-items-center rounded-2xl', file ? 'bg-emerald-100 text-emerald-700' : 'bg-white text-lens-ink shadow-sm')}>{file ? <FileText size={26}/> : <FileUp size={26}/>}</span><p className="mt-4 max-w-full break-all font-bold">{file ? file.name : 'Drop your resume here'}</p><p className="mt-1 text-sm text-slate-500">{file ? `${(file.size / 1024).toFixed(0)} KB · Ready to analyze` : 'or click to browse your files'}</p><span className="mt-4 inline-flex items-center gap-2 rounded-xl bg-lens-ink px-4 py-2.5 text-sm font-bold text-white"><Upload size={15}/>{file ? 'Choose another file' : 'Browse files'}</span>
            </div><div className="mt-4 flex flex-wrap gap-4 text-xs font-semibold text-slate-500"><span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-emerald-600"/> PDF and DOCX</span><span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-emerald-600"/> Up to 5 MB</span></div>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"><div className="mb-6 flex items-center gap-3"><span className="grid size-11 place-items-center rounded-2xl bg-lens-chartreuse text-sm font-black">02</span><div><h3 className="font-extrabold">Job description</h3><p className="mt-1 text-sm text-slate-500">Paste the role you want to apply for.</p></div></div>
            <div className="flex items-center justify-between gap-3 text-[11px] font-extrabold tracking-[.13em] text-slate-500"><label htmlFor="job-description">JOB DESCRIPTION</label><span className="tracking-normal">{jobDescription.length.toLocaleString()} / 15,000</span></div>
            <textarea id="job-description" value={jobDescription} onChange={(event) => { setJobDescription(event.target.value); setError(''); setResult(null) }} placeholder={'Paste the complete job description here...\n\nInclude responsibilities, required skills, preferred qualifications, and education requirements for a more useful comparison.'} minLength={30} maxLength={15000} rows={12} className="mt-3 min-h-64 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm leading-6 text-lens-ink outline-none transition placeholder:text-slate-400 focus:border-lens-lavender focus:bg-white focus:ring-4 focus:ring-lens-lavender/20"/>
            <div className="mt-3 flex flex-wrap justify-between gap-2 text-xs text-slate-500"><span className="flex items-center gap-1.5"><FileText size={13}/> Minimum 30 characters</span><span>{jobDescription.trim().length} characters</span></div>
          </div>
          <div className="flex flex-col gap-4 rounded-3xl bg-lens-ink p-5 text-white sm:flex-row sm:items-center sm:justify-between sm:px-7 lg:col-span-2"><p className="flex items-start gap-2 text-sm leading-6 text-white/75"><ShieldCheck size={18} className="mt-0.5 shrink-0 text-lens-chartreuse"/> Upload only documents you're comfortable analyzing. Your resume isn't stored permanently by this interface.</p><button type="submit" disabled={loading} className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-lens-chartreuse px-5 py-3.5 text-sm font-black text-lens-ink transition hover:brightness-95 disabled:cursor-wait disabled:opacity-70">{loading ? <><LoaderCircle size={17} className="animate-spin"/> Analyzing...</> : <>Analyze resume <ArrowRight size={17}/></>}</button></div>
        </form>
        {error && <div role="alert" className="mt-5 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-900"><CircleAlert size={20} className="mt-0.5 shrink-0"/><div className="flex-1"><p className="font-bold">We couldn't complete the analysis</p><p className="mt-1 text-sm">{error}</p></div><button onClick={() => setError('')} aria-label="Dismiss error"><X size={18}/></button></div>}
        {loading && <div role="status" className="mt-5 rounded-3xl border border-slate-200 bg-white p-8 text-center"><LoaderCircle size={30} className="mx-auto animate-spin text-lens-ink"/><h3 className="mt-4 font-extrabold">Looking beyond the keywords</h3><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Extracting resume content, comparing skills, and finding potentially relevant evidence.</p><p className="mt-3 text-xs text-slate-400">This may take a little while on the first run.</p></div>}
      </section>

      {result && <section id="results" className="scroll-mt-24 pt-14"><div className="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-extrabold tracking-[.16em] text-slate-500">YOUR ANALYSIS</p><h2 className="mt-2 text-2xl font-black tracking-tight sm:text-3xl">Here's your match breakdown.</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Use these insights to identify strengths and areas to work on—not as a hiring prediction.</p></div><span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-800"><CheckCircle2 size={15}/> Analysis complete</span></div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><div className="rounded-3xl bg-lens-ink p-6 text-white sm:col-span-2"><div className="flex items-center gap-2 text-xs font-extrabold tracking-[.13em] text-white/70"><Gauge size={17}/> SKILL COVERAGE</div><div className="mt-4 flex items-baseline gap-2"><strong className="text-6xl font-black tracking-tight">{score === null ? '—' : Math.round(score)}</strong>{score !== null && <span className="text-sm text-white/60">/ 100</span>}</div><div className="mt-5 h-2 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-lens-chartreuse transition-all" style={{ width: `${score ?? 0}%` }}/></div><p className="mt-3 font-bold">{score === null ? 'Score unavailable' : score >= 80 ? 'Strong skill coverage' : score >= 60 ? 'Good starting point' : score >= 40 ? 'Room to improve' : 'More skill alignment needed'}</p><p className="mt-2 max-w-lg text-xs leading-5 text-white/60">Based on the backend matching method. This is not an ATS score or a probability of getting hired.</p></div>
          {[{label:'MATCHED REQUIRED SKILLS',value:matched.length,desc:'Recognized in your resume',icon:CheckCircle2},{label:'SKILL GAPS',value:missing.length,desc:'Required skills not recognized',icon:Target},{label:'EVIDENCE SUGGESTIONS',value:suggestions.length,desc:'Potentially relevant evidence',icon:Sparkles}].map((metric) => <div key={metric.label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><span className="grid size-10 place-items-center rounded-xl bg-slate-100"><metric.icon size={20}/></span><p className="mt-5 text-[10px] font-extrabold tracking-[.12em] text-slate-500">{metric.label}</p><p className="mt-1 text-4xl font-black tracking-tight">{metric.value}</p><p className="mt-1 text-sm text-slate-500">{metric.desc}</p></div>)}
        </div>

        <div className="mt-5 grid gap-5 xl:grid-cols-2"><Card title="Skills breakdown" icon={Zap} count={matched.length + missing.length}><div className="flex flex-wrap gap-2 border-b border-slate-100 pb-4">{tabs.map(tab => <button key={tab.id} type="button" onClick={() => setActiveTab(tab.id)} className={cx('rounded-xl px-3.5 py-2 text-sm font-bold transition', activeTab === tab.id ? 'bg-lens-ink text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')}>{tab.label}<span className="ml-2 rounded-full bg-white/15 px-1.5 py-0.5 text-xs">{tab.count}</span></button>)}</div>
            <div className="mt-5">{activeTab === 'matched' && (matched.length ? <div className="flex flex-wrap gap-2">{matched.map((s,i)=><Pill key={`${skillName(s)}-${i}`} tone="matched">{skillName(s)}</Pill>)}</div> : <p className="text-sm text-slate-500">No confirmed required skill matches were returned.</p>)}{activeTab === 'missing' && (missing.length ? <div className="flex flex-wrap gap-2">{missing.map((s,i)=><Pill key={`${skillName(s)}-${i}`} tone="missing">{skillName(s)}</Pill>)}</div> : <p className="text-sm text-slate-500">No missing required skills were returned.</p>)}{activeTab === 'preferred' && <div className="space-y-5"><div><p className="mb-3 text-sm font-bold">Matched preferred skills</p><div className="flex flex-wrap gap-2">{preferred.length ? preferred.map((s,i)=><Pill key={`${skillName(s)}-${i}`} tone="matched">{skillName(s)}</Pill>) : <span className="text-sm text-slate-500">None returned.</span>}</div></div><div><p className="mb-3 text-sm font-bold">Missing preferred skills</p><div className="flex flex-wrap gap-2">{missingPreferred.length ? missingPreferred.map((s,i)=><Pill key={`${skillName(s)}-${i}`} tone="missing">{skillName(s)}</Pill>) : <span className="text-sm text-slate-500">None returned.</span>}</div></div></div>}</div><p className="mt-6 rounded-2xl bg-lens-lavender/15 p-4 text-xs leading-5 text-slate-600"><Sparkles size={14} className="mr-1 inline"/> A missing skill means the system didn't recognize it in your resume. Confirm your real experience before deciding whether to learn or add anything.</p></Card>
          <Card title="Resume quality" icon={Gauge} count={quality.score !== undefined ? `${quality.score}/100` : undefined}>{quality.score !== undefined ? <><div className="flex items-end gap-3"><span className="text-5xl font-black">{quality.score}</span><span className="mb-1 rounded-full bg-lens-lavender/30 px-3 py-1 text-sm font-bold">{quality.rating || 'Quality indicator'}</span></div><div className="mt-4 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-lens-lavender" style={{width:`${Math.max(0,Math.min(100,Number(quality.score)||0))}%`}}/></div><p className="mt-4 text-sm leading-6 text-slate-600">{quality.score_explanation || 'A heuristic indicator of resume content quality, not an ATS score or hiring prediction.'}</p>{quality.executive_summary && <div className="mt-5 rounded-2xl bg-slate-50 p-4"><p className="text-xs font-extrabold tracking-wider text-slate-500">EXECUTIVE SUMMARY</p><p className="mt-2 text-sm leading-6 text-slate-700">{quality.executive_summary}</p></div>}</> : <p className="text-sm text-slate-500">Resume quality analysis was not included in the API response.</p>}</Card>
        </div>

        <div className="mt-5 grid gap-5 xl:grid-cols-2"><Card title="Top strengths" icon={CheckCircle2} count={strengths.length}>{strengths.length ? <ul className="space-y-4">{strengths.map((item,i)=><li key={`${item.title}-${i}`} className="flex gap-3"><span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-emerald-50 text-emerald-700"><Check size={15}/></span><div><p className="font-bold">{item.title || item}</p>{item.evidence && <p className="mt-1 text-sm leading-6 text-slate-500">{item.evidence}</p>}</div></li>)}</ul> : <p className="text-sm text-slate-500">No strengths were returned by the analyzer.</p>}</Card>
          <Card title="Priority improvements" icon={Lightbulb} count={improvements.length}>{improvements.length ? <ul className="space-y-4">{improvements.map((item,i)=><li key={`${item.title}-${i}`} className="rounded-2xl border border-slate-100 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-bold">{item.title || item}</p>{item.priority && <span className={cx('rounded-full px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider',item.priority==='high'?'bg-rose-50 text-rose-700':item.priority==='medium'?'bg-amber-50 text-amber-800':'bg-slate-100 text-slate-600')}>{item.priority} priority</span>}</div>{item.reason && <p className="mt-2 text-sm leading-6 text-slate-500">{item.reason}</p>}</li>)}</ul> : <p className="text-sm text-slate-500">No improvement suggestions were returned.</p>}</Card>
        </div>

        {metrics.length > 0 && <Card title="Resume performance metrics" icon={Target} className="mt-5"><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{metrics.map((metric,i)=><div key={metric.key || metric.label || i} className="rounded-2xl bg-slate-50 p-4"><div className="flex items-start justify-between gap-3"><p className="text-sm font-bold">{metric.label || metric.key}</p><span className="text-sm font-black">{Math.round(Number(metric.percentage ?? ((metric.score||0)/(metric.max_score||100))*100))}%</span></div><div className="mt-3 h-2 rounded-full bg-slate-200"><div className="h-2 rounded-full bg-lens-ink" style={{width:`${Math.max(0,Math.min(100,Number(metric.percentage ?? ((metric.score||0)/(metric.max_score||100))*100)))}%`}}/></div>{Array.isArray(metric.evidence) && metric.evidence.length>0 && <ul className="mt-3 space-y-1 text-xs leading-5 text-slate-500">{metric.evidence.slice(0,3).map((line,j)=><li key={j}>• {line}</li>)}</ul>}</div>)}</div></Card>}

        <div className="mt-5 grid gap-5 xl:grid-cols-2"><Card title="ATS keyword coverage" icon={Target} count={keywordCoverage !== undefined ? `${Math.round(Number(keywordCoverage))}%` : undefined}>{keywordCoverage !== undefined && <div className="mb-4"><div className="mb-2 flex justify-between text-sm"><span className="font-semibold text-slate-600">Detected keyword coverage</span><strong>{Math.round(Number(keywordCoverage))}%</strong></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-lens-chartreuse" style={{width:`${Math.max(0,Math.min(100,Number(keywordCoverage)||0))}%`}}/></div></div>}<div className="grid gap-4 sm:grid-cols-2"><div><p className="mb-3 text-sm font-bold">Matched keywords</p><div className="flex flex-wrap gap-2">{Array.isArray(matchedKeywords)&&matchedKeywords.length ? matchedKeywords.slice(0,35).map((k,i)=><Pill key={`${typeof k==='string'?k:k.keyword}-${i}`} tone="matched">{typeof k==='string'?k:k.keyword||k.name||'Keyword'}</Pill>) : <span className="text-sm text-slate-500">No keyword list returned.</span>}</div></div><div><p className="mb-3 text-sm font-bold">Missing keywords</p><div className="flex flex-wrap gap-2">{Array.isArray(missingKeywords)&&missingKeywords.length ? missingKeywords.slice(0,35).map((k,i)=><Pill key={`${typeof k==='string'?k:k.keyword}-${i}`} tone="missing">{typeof k==='string'?k:k.keyword||k.name||'Keyword'}</Pill>) : <span className="text-sm text-slate-500">No missing keyword list returned.</span>}</div></div></div><p className="mt-5 text-xs leading-5 text-slate-500">Keyword coverage is an aid for reviewing alignment, not a guarantee of passing an employer's ATS.</p></Card>
          <Card title="Semantic evidence suggestions" icon={Sparkles} count={suggestions.length}>{suggestions.length ? <div className="space-y-3">{suggestions.slice(0,8).map((item,i)=><div key={`${item.requirement||item.skill||'suggestion'}-${i}`} className="rounded-2xl border border-slate-100 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-bold">{item.requirement || item.skill || item.title || 'Relevant evidence'}</p>{item.similarity !== undefined && <span className="rounded-full bg-lens-lavender/25 px-2.5 py-1 text-xs font-bold">Similarity {Math.round(Number(item.similarity)*100)}%</span>}</div>{item.resume_evidence && <p className="mt-2 text-sm leading-6 text-slate-600">{item.resume_evidence}</p>}<p className="mt-2 text-xs text-slate-400">Suggestion only — verify that the evidence accurately represents your experience.</p></div>)}</div> : <p className="text-sm text-slate-500">No semantic suggestions returned. This can be normal if optional semantic matching is unavailable.</p>}</Card>
        </div>
      </section>}

      <section id="how-it-works" className="mt-16 rounded-3xl border border-slate-200 bg-white p-6 sm:p-9"><p className="text-xs font-extrabold tracking-[.16em] text-slate-500">HOW IT WORKS</p><h2 className="mt-2 text-2xl font-black tracking-tight">Three steps. Clearer direction.</h2><div className="mt-6 grid gap-5 md:grid-cols-3">{[{n:'01',title:'Upload your resume',text:'Add a PDF or DOCX file for text extraction.'},{n:'02',title:'Add the target role',text:'Paste the job description to compare its requirements.'},{n:'03',title:'Review your insights',text:'Explore matched skills, gaps, resume quality and keyword clues.'}].map(step=><div key={step.n} className="rounded-2xl bg-slate-50 p-5"><span className="grid size-9 place-items-center rounded-xl bg-lens-chartreuse text-xs font-black">{step.n}</span><h3 className="mt-4 font-extrabold">{step.title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{step.text}</p></div>)}</div></section>
      <footer className="flex flex-col gap-3 border-t border-slate-200 py-8 text-xs leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between"><span>© {new Date().getFullYear()} HireLens AI</span><span>Insights support your review; they do not predict hiring outcomes.</span></footer>
    </main>
  </div>
}
