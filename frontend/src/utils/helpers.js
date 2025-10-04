/**
 * Debounce функция
 */
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Throttle функция
 */
export function throttle(func, limit) {
  let inThrottle
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * Форматирование даты
 */
export function formatDate(date, format = 'default') {
  if (!date) return ''
  
  const d = new Date(date)
  
  switch (format) {
    case 'short':
      return d.toLocaleDateString('ru-RU', { 
        day: 'numeric', 
        month: 'short' 
      })
    
    case 'long':
      return d.toLocaleDateString('ru-RU', { 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric' 
      })
    
    case 'time':
      return d.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    
    case 'datetime':
      return d.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    
    case 'relative':
      return getRelativeTime(d)
    
    default:
      return d.toLocaleDateString('ru-RU')
  }
}

/**
 * Относительное время
 */
export function getRelativeTime(date) {
  const now = new Date()
  const d = new Date(date)
  const diffInSeconds = Math.floor((now - d) / 1000)
  
  if (diffInSeconds < 60) {
    return 'только что'
  }
  
  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (diffInMinutes < 60) {
    return `${diffInMinutes} ${pluralize(diffInMinutes, 'минуту', 'минуты', 'минут')} назад`
  }
  
  const diffInHours = Math.floor(diffInMinutes / 60)
  if (diffInHours < 24) {
    return `${diffInHours} ${pluralize(diffInHours, 'час', 'часа', 'часов')} назад`
  }
  
  const diffInDays = Math.floor(diffInHours / 24)
  if (diffInDays < 7) {
    return `${diffInDays} ${pluralize(diffInDays, 'день', 'дня', 'дней')} назад`
  }
  
  if (diffInDays < 30) {
    const weeks = Math.floor(diffInDays / 7)
    return `${weeks} ${pluralize(weeks, 'неделю', 'недели', 'недель')} назад`
  }
  
  if (diffInDays < 365) {
    const months = Math.floor(diffInDays / 30)
    return `${months} ${pluralize(months, 'месяц', 'месяца', 'месяцев')} назад`
  }
  
  const years = Math.floor(diffInDays / 365)
  return `${years} ${pluralize(years, 'год', 'года', 'лет')} назад`
}

/**
 * Склонение слов
 */
export function pluralize(count, one, few, many) {
  const mod10 = count % 10
  const mod100 = count % 100
  
  if (mod10 === 1 && mod100 !== 11) {
    return one
  }
  
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return few
  }
  
  return many
}

/**
 * Форматирование чисел
 */
export function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K'
  }
  return num.toString()
}

/**
 * Обрезка текста
 */
export function truncate(text, length = 100, suffix = '...') {
  if (!text || text.length <= length) return text
  return text.substring(0, length).trim() + suffix
}

/**
 * Генерация slug
 */
export function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/**
 * Глубокое клонирование объекта
 */
export function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * Проверка на мобильное устройство
 */
export function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

/**
 * Копирование в буфер обмена
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    // Fallback для старых браузеров
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    
    try {
      document.execCommand('copy')
      document.body.removeChild(textArea)
      return true
    } catch (err) {
      document.body.removeChild(textArea)
      return false
    }
  }
}

/**
 * Загрузка изображения с проверкой
 */
export function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

/**
 * Получение расширения файла
 */
export function getFileExtension(filename) {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
}

/**
 * Форматирование размера файла
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Генерация случайного ID
 */
export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

/**
 * Валидация email
 */
export function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

/**
 * Валидация URL
 */
export function isValidUrl(url) {
  try {
    new URL(url)
    return true
  } catch (e) {
    return false
  }
}

/**
 * Получение query параметров
 */
export function getQueryParams(url = window.location.href) {
  const params = {}
  const parser = new URL(url)
  
  for (const [key, value] of parser.searchParams) {
    params[key] = value
  }
  
  return params
}

/**
 * Задержка (для промисов)
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}