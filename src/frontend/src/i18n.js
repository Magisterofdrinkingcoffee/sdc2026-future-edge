// Interface translations: English (key), Bahasa Malaysia (ms), Simplified Chinese (zh).
// Course names, role titles and cited source text stay in English (they are quoted from their sources).
// Anything not in this list falls back to English, so a missing line never breaks the app.
let LANG = 'en'
export const LANGS = [{ id: 'en', label: 'EN' }, { id: 'ms', label: 'BM' }, { id: 'zh', label: '中文' }]
export const setLang = (l) => { LANG = l || 'en' }
export const getLang = () => LANG

const D = {
  // welcome
  'What will AI do to your career in the next 3 years?': { ms: 'Apakah kesan AI terhadap kerjaya anda dalam 3 tahun akan datang?', zh: '未来三年，AI 会如何影响你的职业？' },
  'Upload your CV and get a career forecast: which of your skills AI will take over, which will keep you valuable, and a quest map of small steps to stay ahead.': { ms: 'Muat naik CV anda dan dapatkan ramalan kerjaya: kemahiran mana yang akan diambil alih oleh AI, kemahiran mana yang kekal bernilai, dan peta misi langkah kecil untuk terus mendahului.', zh: '上传你的简历，获得一份职业预测：哪些技能会被 AI 取代，哪些技能会让你保持价值，以及一份帮你保持领先的小步骤任务地图。' },
  'Get my forecast': { ms: 'Dapatkan ramalan saya', zh: '获取我的预测' },
  'Start over with a new CV': { ms: 'Mula semula dengan CV baharu', zh: '用新简历重新开始' },
  'Continue my quests': { ms: 'Teruskan misi saya', zh: '继续我的任务' },
  '🏢 For HR & L&D teams': { ms: '🏢 Untuk pasukan HR & L&D', zh: '🏢 面向人力资源与培训团队' },
  'Takes about 3 minutes. Your CV is read once and not stored.': { ms: 'Mengambil masa kira-kira 3 minit. CV anda dibaca sekali sahaja dan tidak disimpan.', zh: '大约需要 3 分钟。你的简历只读取一次，不会被保存。' },
  "Your Edge Score shows how hard you'll be to replace by AI, from 0 to 100. Each year gets its own forecast.": { ms: 'Skor Edge anda menunjukkan betapa sukarnya anda digantikan oleh AI, dari 0 hingga 100. Setiap tahun mempunyai ramalan tersendiri.', zh: '你的 Edge 分数（0–100）表示你有多难被 AI 取代。每一年都有单独的预测。' },
  "Malaysia's job market is already changing": { ms: 'Pasaran kerja Malaysia sudah pun berubah', zh: '马来西亚的就业市场已经在改变' },
  'Real numbers from the World Economic Forum and the Department of Statistics Malaysia.': { ms: 'Angka sebenar daripada Forum Ekonomi Dunia dan Jabatan Perangkaan Malaysia.', zh: '来自世界经济论坛和马来西亚统计局的真实数据。' },
  'Example: data entry clerk': { ms: 'Contoh: kerani kemasukan data', zh: '示例：数据录入员' },
  'Example': { ms: 'Contoh', zh: '示例' },
  'Interface in your language; course names, job titles and quoted sources stay in English.': { ms: 'Antara muka dalam bahasa anda; nama kursus, jawatan dan sumber yang dipetik kekal dalam Bahasa Inggeris.', zh: '界面已翻译；课程名称、职位名称和引用来源保留英文原文。' },
  // CV step
  'Start with your CV': { ms: 'Mulakan dengan CV anda', zh: '从你的简历开始' },
  'We read it once to find your skills, then throw it away. Your name, email, phone, IC number, age and gender are removed before matching.': { ms: 'Kami membacanya sekali untuk mencari kemahiran anda, kemudian membuangnya. Nama, e-mel, telefon, nombor IC, umur dan jantina anda dibuang sebelum padanan.', zh: '我们只读取一次以找出你的技能，然后立即删除。匹配前会移除你的姓名、邮箱、电话、身份证号码、年龄和性别。' },
  'Drop your CV here': { ms: 'Letakkan CV anda di sini', zh: '把简历拖到这里' },
  'PDF, Word, photo or .txt, max 5 MB. Click to choose a file.': { ms: 'PDF, Word, gambar atau .txt, maksimum 5 MB. Klik untuk memilih fail.', zh: 'PDF、Word、照片或 .txt，最大 5 MB。点击选择文件。' },
  'Or try a sample person': { ms: 'Atau cuba orang contoh', zh: '或者试试示例人物' },
  'Made-up people with made-up CVs. Their PDF goes through the same reader as yours.': { ms: 'Orang rekaan dengan CV rekaan. PDF mereka melalui pembaca yang sama seperti CV anda.', zh: '虚构的人物和简历。他们的 PDF 会经过与你的简历相同的读取流程。' },
  'Use this CV': { ms: 'Guna CV ini', zh: '使用这份简历' },
  'View PDF': { ms: 'Lihat PDF', zh: '查看 PDF' },
  'Find my skills': { ms: 'Cari kemahiran saya', zh: '找出我的技能' },
  'Looking for skills and the sentences that prove them.': { ms: 'Mencari kemahiran dan ayat yang membuktikannya.', zh: '正在寻找技能以及证明这些技能的句子。' },
  'What should we call you?': { ms: 'Apakah nama panggilan anda?', zh: '我们该怎么称呼你？' },
  'Looks right': { ms: 'Nampak betul', zh: '看起来没问题' },
  'Use a different CV': { ms: 'Guna CV lain', zh: '换一份简历' },
  'Missing a skill? Add it…': { ms: 'Ada kemahiran yang tiada? Tambahkannya…', zh: '缺少某项技能？添加它…' },
  'Add': { ms: 'Tambah', zh: '添加' },
  'Added by you': { ms: 'Ditambah oleh anda', zh: '由你添加' },
  'Fairness check passed:': { ms: 'Semakan keadilan lulus:', zh: '公平性检查通过：' },
  // goal step
  'Where do you want to be?': { ms: 'Di manakah anda mahu berada?', zh: '你想去哪里？' },
  'Not sure yet, suggest one for me': { ms: 'Belum pasti, cadangkan untuk saya', zh: '还不确定，帮我推荐一个' },
  "We'll pick the role where you'll have the strongest edge in 3 years, skipping roles AI is taking over.": { ms: 'Kami akan memilih peranan di mana anda paling kukuh dalam 3 tahun, tanpa peranan yang sedang diambil alih oleh AI.', zh: '我们会挑选三年后你最有优势的职位，并跳过正在被 AI 取代的职位。' },
  // quiz
  'Catch the AI': { ms: 'Tangkap AI', zh: '找出 AI 的错误' },
  'About 2 minutes. This is an estimate to guide you, never a hiring decision.': { ms: 'Kira-kira 2 minit. Ini anggaran untuk membimbing anda, bukan keputusan pengambilan pekerja.', zh: '大约 2 分钟。这只是帮助你的估计，绝不是招聘决定。' },
  'Start': { ms: 'Mula', zh: '开始' },
  'Skip for now': { ms: 'Langkau buat masa ini', zh: '暂时跳过' },
  "Tap every line you wouldn't send as it is.": { ms: 'Ketik setiap baris yang anda tidak akan hantar seperti sedia ada.', zh: '点出每一行你不会原样发送的内容。' },
  'Done checking': { ms: 'Selesai menyemak', zh: '检查完毕' },
  'How sure are you that you found every mistake?': { ms: 'Sejauh manakah anda pasti telah menemui setiap kesilapan?', zh: '你有多确定自己找到了所有错误？' },
  'Good judgment includes knowing what you might have missed.': { ms: 'Pertimbangan yang baik termasuk mengetahui apa yang mungkin anda terlepas.', zh: '好的判断力包括知道自己可能遗漏了什么。' },
  'Just guessing': { ms: 'Sekadar meneka', zh: '只是猜测' },
  'Completely sure': { ms: 'Sangat pasti', zh: '完全确定' },
  'Next': { ms: 'Seterusnya', zh: '下一步' },
  'Two quick situations': { ms: 'Dua situasi ringkas', zh: '两个简短情境' },
  'See my result': { ms: 'Lihat keputusan saya', zh: '查看我的结果' },
  'What the AI got wrong': { ms: 'Apa yang AI silap', zh: 'AI 错在哪里' },
  'See my forecast': { ms: 'Lihat ramalan saya', zh: '查看我的预测' },
  'Loading…': { ms: 'Memuatkan…', zh: '加载中…' },
  // reveal
  'Building your forecast…': { ms: 'Membina ramalan anda…', zh: '正在生成你的预测…' },
  'Your One Move': { ms: 'Satu Langkah Anda', zh: '你的关键一步' },
  'Working it out…': { ms: 'Sedang mengira…', zh: '计算中…' },
  'Start my quests': { ms: 'Mulakan misi saya', zh: '开始我的任务' },
  // dashboard
  'Quests': { ms: 'Misi', zh: '任务' },
  'Forecast': { ms: 'Ramalan', zh: '预测' },
  'Me': { ms: 'Saya', zh: '我' },
  'Drawing your quest map…': { ms: 'Melukis peta misi anda…', zh: '正在绘制你的任务地图…' },
  'Start here': { ms: 'Mula di sini', zh: '从这里开始' },
  'I finished this quest': { ms: 'Saya telah selesai misi ini', zh: '我完成了这个任务' },
  'Mark as not done': { ms: 'Tanda belum selesai', zh: '标记为未完成' },
  '🔒 Finish the quest before this one to unlock it.': { ms: '🔒 Selesaikan misi sebelum ini untuk membukanya.', zh: '🔒 完成前一个任务即可解锁。' },
  'Badges': { ms: 'Lencana', zh: '徽章' },
  'XP history': { ms: 'Sejarah XP', zh: '经验值记录' },
  'Play Catch the AI again': { ms: 'Main Tangkap AI sekali lagi', zh: '再玩一次“找出 AI 的错误”' },
  'Update my CV': { ms: 'Kemas kini CV saya', zh: '更新我的简历' },
  'Start over': { ms: 'Mula semula', zh: '重新开始' },
  'day streak': { ms: 'hari berturut-turut', zh: '天连续' },
  // forecast
  'How hard you\'ll be to replace by AI, from 0 to 100. Estimates, not a verdict.': { ms: 'Betapa sukarnya anda digantikan oleh AI, dari 0 hingga 100. Anggaran, bukan keputusan muktamad.', zh: '你有多难被 AI 取代（0–100）。这是估计，不是定论。' },
  'How we worked this out': { ms: 'Cara kami mengiranya', zh: '我们是如何计算的' },
  'Your skills over the next 3 years': { ms: 'Kemahiran anda dalam 3 tahun akan datang', zh: '未来三年你的技能变化' },
  'Growing in value': { ms: 'Semakin bernilai', zh: '价值上升' },
  'Holding steady': { ms: 'Kekal stabil', zh: '保持稳定' },
  'At risk from AI': { ms: 'Berisiko daripada AI', zh: '面临 AI 风险' },
  'Other roles for you': { ms: 'Peranan lain untuk anda', zh: '适合你的其他职位' },
  'Job demand by 2030': { ms: 'Permintaan kerja menjelang 2030', zh: '2030 年岗位需求' },
  'Typical pay': { ms: 'Gaji biasa', zh: '典型薪资' },
  "Malaysia's critical jobs list": { ms: 'Senarai pekerjaan kritikal Malaysia', zh: '马来西亚紧缺职业清单' },
  '🌍 Your path and the Sustainable Development Goals': { ms: '🌍 Laluan anda dan Matlamat Pembangunan Mampan', zh: '🌍 你的职业道路与可持续发展目标' },
  'Why it matters:': { ms: 'Mengapa ia penting:', zh: '为什么重要：' },
  'What do you want your work to help with?': { ms: 'Apakah yang anda mahu kerja anda bantu?', zh: '你希望你的工作帮助解决什么？' },
  'Pick any. Roles that serve these goals move up your list and are shown below. Your Edge Score itself never changes – it only measures how hard you are to replace.': { ms: 'Pilih mana-mana. Peranan yang menyumbang kepada matlamat ini naik dalam senarai anda dan dipaparkan di bawah. Skor Edge anda sendiri tidak berubah – ia hanya mengukur betapa sukarnya anda digantikan.', zh: '可多选。服务于这些目标的职位会在列表中上移并显示在下方。你的 Edge 分数本身不会改变——它只衡量你有多难被取代。' },
  'Make this my goal': { ms: 'Jadikan matlamat saya', zh: '设为我的目标' },
  // team
  '🏢 Team view for HR & L&D': { ms: '🏢 Paparan pasukan untuk HR & L&D', zh: '🏢 人力资源与培训团队视图' },
  '+ Add CVs': { ms: '+ Tambah CV', zh: '+ 添加简历' },
  'Clear team': { ms: 'Kosongkan pasukan', zh: '清空团队' },
  'One reskilling plan for the team': { ms: 'Satu pelan latihan semula untuk pasukan', zh: '团队统一再培训计划' },
  '🌍 Team SDG contribution': { ms: '🌍 Sumbangan SDG pasukan', zh: '🌍 团队对可持续发展目标的贡献' },
  '‹ Back': { ms: '‹ Kembali', zh: '‹ 返回' },
  'We found {n} skills': { ms: 'Kami menemui {n} kemahiran', zh: '我们找到了 {n} 项技能' },
  'Check each level. We guessed it from how you described it.': { ms: 'Semak setiap tahap. Kami menekanya berdasarkan cara anda menerangkannya.', zh: '请检查每项的水平。这是我们根据你的描述推测的。' },
  'Removed before matching:': { ms: 'Dibuang sebelum padanan:', zh: '匹配前已移除：' },
  '{name}, here\'s your forecast as {role}': { ms: '{name}, ini ramalan anda sebagai {role}', zh: '{name}，这是你作为 {role} 的预测' },
  'Here\'s your forecast as {role}': { ms: 'Ini ramalan anda sebagai {role}', zh: '这是你作为 {role} 的预测' },
  'Your quests to {role}': { ms: 'Misi anda ke arah {role}', zh: '通往 {role} 的任务' },
  'Career forecast: {role}': { ms: 'Ramalan kerjaya: {role}', zh: '职业预测：{role}' },
}

export function t(en, vars) {
  let out = LANG === 'en' ? en : (D[en]?.[LANG] || en)
  if (vars) for (const [k, v] of Object.entries(vars)) out = out.split(`{${k}}`).join(v)
  return out
}
