from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.research_members import MemberRole, ResearchMember
from app.models.research_project import ResearchProject
from app.models.user import User
from app.schemas.research_member import ResearchMemberCreate
from app.schemas.research_project import ResearchProjectBase, ResearchProjectUpdate


class ResearchProjectService:
    @staticmethod
    def _check_permission(
        db: Session,
        project_id: int,
        user_id: int,
        require_owner: bool = False,
    ) -> tuple[ResearchProject, ResearchMember]:

        # kiểm tra quyền truy cập dự án:
        # kiểm tra đề tài tồn tại không (404)
        # kiểm tra user có phải là thành viên không (403)
        # nếu require_owner=True, kiểm tra user có phải là OWNER không (403)

        project = (
            db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy đề tài nghiên cứu",
            )

        member = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id,
                ResearchMember.user_id == user_id,
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không phải là thành viên của đề tài nghiên cứu này",
            )

        if require_owner and member.role != MemberRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ OWNER mới có quyền thực hiện thao tác này",
            )

        return project, member

    @staticmethod
    def create(
        db: Session, project_in: ResearchProjectBase, owner_id: int
    ) -> ResearchProject:
        """Tạo đề tài mới và tự động gán vai trò OWNER cho người tạo"""
        db_project = ResearchProject(
            name=project_in.name,
            description=project_in.description,
            owner_id=owner_id,
        )
        db.add(db_project)
        db.flush()

        db_member = ResearchMember(
            project_id=db_project.id, user_id=owner_id, role=MemberRole.OWNER
        )
        db.add(db_member)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_my_project(
        db: Session, user_id: int, search: str | None = None
    ) -> list[ResearchProject]:
        """Lấy danh sách đề tài mà user là OWNER hoặc MEMBER"""
        query = (
            db.query(ResearchProject)
            .join(ResearchMember, ResearchMember.project_id == ResearchProject.id)
            .filter(ResearchMember.user_id == user_id)
        )

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(ResearchProject.name.ilike(pattern))

        return query.all()

    @staticmethod
    def get_by_id(db: Session, project_id: int, user_id: int) -> ResearchProject:
        """Xem chi tiết đề tài (chỉ thành viên)"""
        project, _ = ResearchProjectService._check_permission(db, project_id, user_id)
        return project

    @staticmethod
    def update(
        db: Session, project_id: int, project_in: ResearchProjectUpdate, user_id: int
    ) -> ResearchProject:
        """Cập nhật đề tài (chỉ OWNER)"""
        project, _ = ResearchProjectService._check_permission(
            db, project_id, user_id, require_owner=True
        )

        update_data = project_in.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            return project

        for key, value in update_data.items():
            setattr(project, key, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, project_id: int, user_id: int) -> None:
        """Xóa đề tài (chỉ OWNER)"""
        project, _ = ResearchProjectService._check_permission(
            db, project_id, user_id, require_owner=True
        )
        db.delete(project)
        db.commit()

    #  Members

    @staticmethod
    def get_members(db: Session, project_id: int, user_id: int) -> list[ResearchMember]:
        """Xem danh sách thành viên (chỉ thành viên)"""
        ResearchProjectService._check_permission(db, project_id, user_id)
        return (
            db.query(ResearchMember)
            .filter(ResearchMember.project_id == project_id)
            .all()
        )

    @staticmethod
    def add_member(
        db: Session,
        project_id: int,
        member_in: ResearchMemberCreate,
        current_user_id: int,
    ) -> ResearchMember:
        """Thêm thành viên (chỉ OWNER)"""
        member = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id,
                ResearchMember.user_id == current_user_id,
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không phải Owner",
            )

        # Kiểm tra user cần thêm có tồn tại không
        target_user = db.query(User).filter(User.id == member_in.user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng cần thêm vào đề tài",
            )

        # Kiểm tra đã là thành viên chưa
        existing = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id,
                ResearchMember.user_id == member_in.user_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người dùng này đã là thành viên của đề tài nghiên cứu",
            )

        new_member = ResearchMember(
            project_id=project_id,
            user_id=member_in.user_id,
            role=member_in.role,
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        return new_member

    @staticmethod
    def remove_member(
        db: Session,
        project_id: int,
        target_user_id: int,
        current_user_id: int,
    ) -> None:
        """Xóa thành viên (chỉ OWNER, không thể xóa OWNER cuối cùng)"""
        ResearchProjectService._check_permission(
            db, project_id, current_user_id, require_owner=True
        )

        member_to_remove = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id,
                ResearchMember.user_id == target_user_id,
            )
            .first()
        )
        if not member_to_remove:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thành viên không thuộc đề tài nghiên cứu này",
            )

        # Không cho xóa OWNER cuối cùng
        if member_to_remove.role == MemberRole.OWNER:
            owner_count = (
                db.query(ResearchMember)
                .filter(
                    ResearchMember.project_id == project_id,
                    ResearchMember.role == MemberRole.OWNER,
                )
                .count()
            )
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không thể xóa OWNER cuối cùng của đề tài nghiên cứu",
                )

        db.delete(member_to_remove)
        db.commit()
