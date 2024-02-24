import mysql from 'mysql2'

const pool = mysql.createPool({
    host: '127.0.0.1',
    user: 'root',
    password: 'thegreat',
    database: 'our_users',
  }).promise()

export  async function getAllnotes() {
    const [rows] = await pool.query("select * from posts")
    return rows
  }
  
export  const products = await getAllnotes()
console.log(products)

