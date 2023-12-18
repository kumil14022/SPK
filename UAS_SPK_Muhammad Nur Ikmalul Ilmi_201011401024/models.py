from sqlalchemy import Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Karyawan(Base):
    __tablename__ = 'data_calon_karyawan'
    id: Mapped[str] = mapped_column(primary_key=True)
    umur: Mapped[int] = mapped_column()
    jenis_kelamin: Mapped[int] = mapped_column()
    status_pernikahan: Mapped[int] = mapped_column()
    pengalaman: Mapped[int] = mapped_column()
    pengetahuan : Mapped[int] = mapped_column()
    
    def __repr__(self) -> str:
        return f"Karyawan(id={self.id!r}, nama={self.nama!r})"
